# Лабораторная работа №3. Транслятор и модель процессора

* P3208. Коломиец Никита Сергеевич
* ```forth | stack | harv | hw | instr | struct | trap | mem | pstr | prob5 ```

## Язык программирования

```text
<label> ::= ([a-z] | [A-Z])+ ([a-z] | [A-Z] | [0-9])*

<program> ::= <word> | <program> " " <program> | <conditional_operator> 
                     | <do_loop_operator> | <begin_until_operator> <init_variable>

<procedure> ::= ": " <label> " ;"

<init_variable> ::= "variable " <label> (" allot " [0-9])?

<conditional_operator> ::= "if " <program> (" else " <program>)? " then"

<do_loop_operator> ::= "do " <program> " loop"

<begin_until_operator> ::= "begin " <program> " loop"

<word> ::= <label> | <math_operand> | <print_string> | [0-9] 
		   | "mod" | "drop" | "over" | "dup" | "read" | "omit" 
                   | "@" | "!" | "ei" | "di"

<math_operand> ::= "+" | "-" | "*" | "/" | "=" | "<" | ">" 

<print_string> ::= ". " <label>
```

Код выполняется последовательно за исключением процедур.
Вызов процедуры осуществляется при указании в программе её названия. Комментарии не предусмотрены.

Пользователь можно объявлять процедуры и потом вызывать их. Пример процедуры:
```text
: gcd dup 0 =
  if
  drop
  else
  swap over mod gcd
  then ;
```

Ниже описаны основные стековые операции в виде

* ```+``` - (n1 n2 -- n3)
* ```-``` - (n1 n2 -- n3)
* ```*``` - (n1 n2 -- n3)
* ```/``` - (n1 n2 -- n3)
* ```=``` - (n1 n2 -- n3)
* ```>``` - (n1 n2 -- n3)
* ```<``` - (n1 n2 -- n3)
* ```mod``` - (n1 n2 -- n3)
* ```drop``` - (n1 -- )
* ```swap``` - (n1 n2 -- n2 n1)
* ```over``` - (n1 n2 -- n1 n2 n1)
* ```dup``` - (n1 -- n1 n1)
* ```key``` - (n1 -- n2)
* ```omit``` - (n1 n2 -- )
* ```read``` - (n1 -- n2)
* ```!``` - (n1 n2 -- )
* ```@``` - (n1 -- n2)
* ```ei``` - ( -- )
* ```di``` - ( -- )

Код подразумевает использование условных переходов:
* ```if```
* ```do``` ```loop```
* ```begin``` ```until```

Условный оператор ```if``` выполняется в зависимости от истинности значения на вершине стека.
Истинным значением является любое целое числа за исключением 0. Ложным значением является 0.

Оператор цикла ```do loop``` выполняет ```K``` итераций в зависимости от двух значений на вершине стека (n1 n2);
```K = n1 - n2```. Внутри конструкции ```do loop``` возможно использовать
переменную ```i```, ```i = n2 + <номер итерации>```.
Аналогично конструкции ```for (i = n2; i < n1; i++) {}``` в алгоритмическом языке программирования

Оператор цикла ```begin until``` выполняет итерации до момента, когда на вершине стека
по достижению конструкции until не будет лежать истинное значение (отличное от нуля).

Оператор объявления переменной ```variable``` создаёт переменную и сопоставляет ей
определенную ячейку памяти, взаимодействовать с которой возможно при помощи ```!``` и ```@```.
В случае добавления ключевого слова ```allot``` выделяется непрерывный участок памяти с фиксированным
в программе размером.

Про переменные читать память команд и транслятор.


## Организация памяти

- Память данных и команд раздельна. Размерность - 32 бита
- Программисту в явном виде доступен исключительно стек данных и память, зарезервированная
  под переменные
- Память данных и команд выделяется статически при запуске модели(а именно в control unit)
- Доступен один вид прерываний - его обработчик лежит по адресу 01 в памяти команд
- Процедуры хранятся в памяти последовательно после прерываний.
- Машинная команда может использоваться как с аргументами (адрес/значение), так и без них.
- Ввиду специфики варианта, числовые и строковые литералы записываются в память данных в
  момент исполнения программы, а не при запуске модели с помощью команд с Immediate Value.
  Формирование команд для записи строковых литералов -- на этапе трансляции
- Все переменные хранятся статически в памяти данных
- Используется стек данных и стек возврата, они являются отдельным физическим устройством
  по отношению к памяти данных и команд

Память команд:

Память команд представляет собой адресное пространство от 00 до 15000, где с 01 ячейки размещаются interrupt handler ы,
после чего идут уже обычные команды

```text

  00       jmp N              
  01       interrupt handle   
       ...                    
  N - 1    interrupt handle   
 -----------------------------
  N        program            
  N + 1    program            
       ...                    
  15000    program            
```

Память данных(идет снизу вверх) представляет собой адресное пространство от 00 до 15000, где от 00 до 511 хранятся
строковые литералы, все остальное выделено под переменные

```text
  00       string literals    
  01       string literals    
       ...                    
  511      strings literal      
+-----------------------------
  512      variables          
  513      variables          
       ...                    
  15000    variables            
```

## Система команд

### Цикл исполнения команды

- Выборка инструкции (без сохранения информации в промежуточные регистры)
- Исполнение команды
- Проверка на прерывание (если прерывание, сохранение PC в Return Stack, переход к обработчику прерывания)

### Кодирование инструкций

Инструкции кодируются в бинарном виде. Идет преобразование номера opcode, индекса в памяти и аргумента в json 

```python
import json

def write_code(filename: str, code: list[dict]):
    with open(filename, "w", encoding="utf-8") as file:
        buf = []
        for instr in code:
            buf.append(json.dumps(instr))
        file.write("[" + ",\n ".join(buf) + "]")
```

В данной конструкции аргумент опционален и может быть упущен в зависимости от типа команды.

## Транслятор

Интерфейс командной строки `translator.py <input_file> <target_file>`

Трансляция происходит в несколько этапов:

1. Разбиение исходного текста программы в набор термов (1 слово = 1 терм)
2. Валидация полученных термов (циклы, процедуры, условные операторы)
3. Трансляция термов в машинные команды (1 терм = N команд)
4. Линковка

При разбиении исходного текста на term необходимо поместить первой командой entry point, после чего разбиваем наш текст
на разделители и сравниваем получившиеся слова с существующими term  
После преобразования слов в term необходимо проверить, что все парные термы полны, то есть

* терму `DO` должен соответствовать последующий терм `LOOP`
* терму `BEGIN` должен соответствовать последующий терм `UNTIL`
* терму `IF` должен соответствовать последующий терм `THEN`, между ними может располагаться терм `ELSE`
* терму `:` должен соответствовать последующий терм `;`
* терму `:intr` должен соответствовать последующий терм `;`
* объявление переменной должно иметь вид `variable <name> [allot <int>]`

Для трансляции Term в набор opcode используется функция:

```text
  list[Term] -> list[list[Opcode]] -> list[Opcode] 
```

Первые два списка имеют одинаковую длину, во втором преобразовании происходит "распрямление"
полученного списка списков машинных команд.

### Линковка

Линковка требует отдельного внимания, потому что необходимо на этапе валидации каждому терму `IF`, `DO`, `:`, `ELSE`
поставить в соответствие дополняющий его терм.
Подобная процедура выполняется также для `variable`, `allot`.  
Таким образом, получается список операций, некоторые из которых могут ссылаться на другие.

Для преобразования этой структуры в последовательный список термов необходимо провести их
линковку, т.е. заменить адреса на термы адресами на машинные команды. Для этого используются различные
варианты адресации внутри машинных команд (абсолютная -- на конкретный терм и относительная -- по отношению к текущему
терму).
Реализуется функцией
```python
def fix_addresses_in_opcodes(term_opcodes: list[list[Opcode]]) -> list[Opcode]:
    result_opcodes = []
    pref_sum = [0]
    for term_num, opcodes in enumerate(term_opcodes):
        term_opcode_cnt = len(opcodes)
        pref_sum.append(pref_sum[term_num] + term_opcode_cnt)
    for term_opcode in list(filter(lambda x: x is not None, term_opcodes)):
        for opcode in term_opcode:
            for param_num, param in enumerate(opcode.params):
                if param.param_type is OpcodeParamType.ADDR:
                    opcode.params[param_num].value = pref_sum[param.value]
                    opcode.params[param_num].param_type = OpcodeParamType.CONST
                if param.param_type is OpcodeParamType.ADDR_REL:
                    opcode.params[param_num].value = len(result_opcodes) + opcode.params[param_num].value
                    opcode.params[param_num].param_type = OpcodeParamType.CONST
            result_opcodes.append(opcode)
    return result_opcodes
```

Остановимся подробнее на строковых литералах.
Так как целочисленные литералы преобразуются в машинную команду `PUSH <int>`, было
решено применить ради простоты модели процессора подобный механизм и для строк.
Строковые литералы в языке Forth используются сразу для вывода их на внешние устройства,
следовательно, строковый литерал вида `." string"` будет развернут в последовательность команд,
выполняющие следующие действия:

* запись в память данных размера строки (prefix-strings)
* посимвольная запись содержимого строки в память данных
* цикл, который осуществляет вывод строки


## Модель процессора

Интерфейс командной строки: `machine.py <machine_code_file> <input_file>`

Реализовано в модуле: [machine.py](machine.py).

Stack Controller:
![TOS](/figure/tos.png)

DataPath:
![DataPath](/figure/datapath.png)

ControlUnit:
![TOS](/figure/controlunit.png)

Stack Controller является частью DataPath и предназначен для упрощения схемы, в коде включен в
класс DataPath

Память:

* `Data Memory` -- однопортовая память данных
* `Instruction Memory` -- однопортовая память команд (Read Only)
* `Data Stack` -- стек для хранения данных программы (доступен программисту)
* `Return Stack` -- стек для хранения адресов возврата и переменной цикла

В модели процессора предусмотрены следующие регистры (недоступны для программиста):

* `SP` -- адрес верхушки стека данных минус два верхних элемента
* `I` -- адрес верхушки стека возврата
* `PC` -- адрес указывающий на текущую исполняемую команду
* `PS` -- состояние программы, 3 бита: разрешены ли прерывания и есть ли запрос на прерывания, находится ли в прерывании
* `TOP` -- значение на верхушке стека
* `NEXT` -- значение второго элемента сверху на стеке
* `TEMP` -- предназначен для эффективного выполнения операций на стеке

В рамках текущей реализации процессора приведем более подробную таблицу с описанием реализуемой системы команд.

| Инструкция                          | Действия процессора                                                   |
|:------------------------------------|:----------------------------------------------------------------------|
| mul, div, sub, add, mod, eq, gr, ls | TOP = TOP x NEXT; SP -= 1; NEXT = MEM                                 |
| drop                                | TOP = NEXT; SP -= 1; NEXT = MEM                                       |
| swap                                | TEMP = TOP; TOP = NEXT; NEXT = TEMP                                   |
| over                                | MEM = NEXT; TEMP = TOP; SP += 1; TOP = NEXT; NEXT = TEMP              |
| dup                                 | MEM = NEXT; NEXT = TOP; SP += 1                                       |
| store                               | DATA_MEM = NEXT; SP -= 1; NEXT = MEM; TOP = NEXT; SP -= 1; NEXT = MEM |
| load                                | TOP = DATA_MEM                                                        |
| push                                | MEM = NEXT; SP += 1; NEXT = TOP; TOP = IMMEDIATE                      |
| pop                                 | =EMP = TOP; TOP = NEXT; SP -= 1; NEXT = MEM; RET_STACK = TEMP; I += 1 |
| rpop                                | I -= 1; TEMP = RET_STACK; MEM = NEXT; NEXT = TOP; SP += 1; TOP = TEMP |
| jmp                                 | PC = IMMEDIATE                                                        |
| zjmp                                | PC = IMMEDIATE; TOP = NEXT; SP -= 1; NEXT = MEM                       |
| call                                | RETURN_STACK = PC; I += 1; PC = IMMEDIATE                             |
| ret                                 | I -= 1; PC = RET_STACK                                                |
  

### Цикл исполнения команды

1. Выборка инструкции (без сохранения информации в промежуточные регистры)
2. Исполнение команды (количество тактов необходимых для исполнения указано в таблице ниже)
3. Проверка на прерывание (если прерывание, сохранение PC в Return Stack, переход к обработчику прерывания)

## Тестирование

В качестве тестов использовано четыре алгоритма:

1. [alice](examples/forth/alice.fth)
2. [cat](examples/forth/cat.fth)
3. [hello-world](examples/forth/hello.fth)
4. [prob5](examples/forth/prob5.fth)

Интеграционные тесты реализованы в модуле [integration_test](./integration_test.py) в виде golden тестов:

CI при помощи Github Action:

``` yaml
name: Translator Model Python CI

on:
  push:
    branches:
      - master
    paths:
      - ".github/workflows/*"
      - "Translator-Model/**"
  pull_request:
    branches:
      - master
    paths:
      - ".github/workflows/*"
      - "Translator-Model/**"

defaults:
  run:
    working-directory: ./Translator-Model

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.11
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install poetry
          poetry install
      - name: Run tests and collect coverage
        run: |
          poetry run coverage run -m pytest .
          poetry run coverage report -m
        env:
          CI: true

  lint:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.11
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install poetry
          poetry install
      - name: Check code formatting with Ruff
        run: poetry run ruff format --check .
      - name: Run Ruff linters
        run: poetry run ruff check .
```

где:

* `poetry` -- управления зависимостями для языка программирования Python.
* `coverage` -- формирование отчёта об уровне покрытия исходного кода.
* `pytest` -- утилита для запуска тестов.
* `ruff` -- утилита для форматирования и проверки стиля кодирования.

Пример проверки исходного кода:

Пример вывода golden test
```text
collected 4 items

integration_test.py::test_translator_and_machine[golden/alice.yml] PASSED                                                                      [ 25%]
integration_test.py::test_translator_and_machine[golden/cat.yml] PASSED                                                                        [ 50%]
integration_test.py::test_translator_and_machine[golden/hello.yml] PASSED                                                                      [ 75%]
integration_test.py::test_translator_and_machine[golden/prob5.yml] PASSED                                                                      [100%]

================================================================= 4 passed in 1.82s ================================================================= 
```

## Аналитика
```text
| ФИО                                | алг     | LoC | code байт | code инстр. | инстр. | такт. | вариант                                                                |
| Коломиец Никита Сергеевич          | alice   |  20 |     -     |    218      |   1985 |   -   | forth | stack | harv | hw | instr | binary | trap | mem | pstr | prob5 | 
| Коломиец Никита Сергеевич          | cat     |  8  |     -     |     21      |   423  |   -   | forth | stack | harv | hw | instr | binary | trap | mem | pstr | prob5 | 
| Коломиец Никита Сергеевич          | hello   |  1  |     -     |     58      |   261  |   -   | forth | stack | harv | hw | instr | binary | trap | mem | pstr | prob5 | 
| Коломиец Никита Сергеевич          | prob5   |  24 |     -     |     126     |   1887 |   -   | forth | stack | harv | hw | instr | binary | trap | mem | pstr | prob5 | 

где:

алг. -- название алгоритма (hello, cat, или как в варианте)

прог. LoC -- кол-во строк кода в реализации алгоритма

code байт -- кол-во байт в машинном коде (если бинарное представление)

code инстр. -- кол-во инструкций в машинном коде

инстр. -- кол-во инструкций, выполненных при работе алгоритма

такт. -- кол-во тактов, которое заняла работа алгоритма
```

