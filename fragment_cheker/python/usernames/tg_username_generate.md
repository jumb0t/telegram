## **Формат:** `@<a-z>_<a-z>_<a-z>`

**Команда Bash:**

```bash
for i in {a..z}; do for j in {a..z}; do for k in {a..z}; do printf "@%s_%s_%s\n" $i $j $k; done; done; done > logins.txt
```

**Пример вывода:**

```
@a_a_a
@a_a_b
@a_a_c
...
@z_z_y
@z_z_z
```

---

## **Формат:** `@<a-z>_<a-z>_<0-9>`

**Команда Bash:**

```bash
for i in {a..z}; do for j in {a..z}; do for k in {0..9}; do printf "@%s_%s_%s\n" $i $j $k; done; done; done > logins.txt
```

**Пример вывода:**

```
@a_a_0
@a_a_1
@a_a_2
...
@z_z_9
```

---

## **Формат:** `@<a-z>_<0-9>_<a-z>`

**Команда Bash:**

```bash
for i in {a..z}; do for j in {0..9}; do for k in {a..z}; do printf "@%s_%s_%s\n" $i $j $k; done; done; done > logins.txt
```

**Пример вывода:**

```
@a_0_a
@a_0_b
@a_0_0
...
@z_9_z
```

---

## **Формат:** `@<a-z>_<0-9>_<0-9>`

**Команда Bash:**

```bash
for i in {a..z}; do for j in {0..9}; do for k in {0..9}; do printf "@%s_%s_%s\n" $i $j $k; done; done; done > logins.txt
```

**Пример вывода:**

```
@a_0_0
@a_0_1
@a_0_2
...
@z_9_9
```

---

## **Формат:** `@<a-z><0-9><0-9><0-9><0-9>`

Этот формат логина состоит из одной буквы и четырех цифр, без разделителей.

**Команда Bash:**

```bash
for i in {a..z}; do for j in {0..9}; do for k in {0..9}; do for l in {0..9}; do for m in {0..9}; do printf "@%s%s%s%s%s\n" $i $j $k $l $m; done; done; done; done; done > logins.txt
```

**Пример вывода:**

```
@a0000
@a0001
@a0002
...
@z9999
```

---

## **Формат:** `@<a-z><a-z><0-9><0-9><0-9>`

Этот формат логина состоит из двух букв и трех цифр, без разделителей.

**Команда Bash:**

```bash
for i in {a..z}; do for j in {a..z}; do for k in {0..9}; do for l in {0..9}; do for m in {0..9}; do printf "@%s%s%s%s%s\n" $i $j $k $l $m; done; done; done; done; done > logins.txt
```

**Пример вывода:**

```
@aa000
@aa001
@aa002
...
@zz999
```

---

## **Формат:** `@<a-z><a-z><a-z><a-z><0-9>`

Этот формат логина состоит из четырех букв и одной цифры, без разделителей.

**Команда Bash:**

```bash
for i in {a..z}; do for j in {a..z}; do for k in {a..z}; do for l in {a..z}; do for m in {0..9}; do printf "@%s%s%s%s%s\n" $i $j $k $l $m; done; done; done; done; done > logins.txt
```

**Пример вывода:**

```
@aaaa0
@aaaa1
@aaaa2
...
@zzzz9
```

---

## **Формат:** `@<a-z><a-z><a-z><0-9><0-9>`

Этот формат логина состоит из трех букв и двух цифр.

**Команда Bash:**

```bash
for i in {a..z}; do for j in {a..z}; do for k in {a..z}; do for l in {0..9}; do for m in {0..9}; do printf "@%s%s%s%s%s\n" $i $j $k $l $m; done; done; done; done; done > logins.txt
```

**Пример вывода:**

```
@aaa00
@aaa01
@aaa02
...
@zzz99
```

---

## **Формат:** `@<a-z><a-z><0-9><0-9><0-9>`

Этот формат логина состоит из двух букв и трех цифр, без разделителей.

**Команда Bash:**

```bash
for i in {a..z}; do for j in {a..z}; do for k in {0..9}; do for l in {0..9}; do for m in {0..9}; do printf "@%s%s%s%s%s\n" $i $j $k $l $m; done; done; done; done; done > logins.txt
```

**Пример вывода:**

```
@aa000
@aa001
@aa002
...
@zz999
```



## **Формат:** `@tg<a-z><a-z><a-z>`

Этот формат логина состоит из фиксированного префикса `@tg`, за которым следуют три буквы латинского алфавита в нижнем регистре.

**Команда Bash:**

```bash
for a in {a..z}; do for b in {a..z}; do for c in {a..z}; do printf "@tg%s%s%s\n" $a $b $c; done; done; done > logins.txt
```

**Пример вывода:**

```
@tgaaa
@tgaab
@tgabc
...
@tgzzz
```

**Объяснение работы команды:**
1. **Фиксированный префикс:**  
   Каждая строка начинается с фиксированного текста `@tg`.

2. **Генерация буквенных комбинаций:**  
   - Первая буква (`a`) перебирается от `a` до `z`.
   - Вторая буква (`b`) также перебирается от `a` до `z` для каждой первой буквы.
   - Третья буква (`c`) перебирается аналогично.

3. **Сохранение результата:**  
   Все сгенерированные строки записываются в файл `logins.txt`.

**Общее количество логинов:**
- 26³ = **17,576 логинов**, от `@tgaaa` до `@tgzzz`.







```bash
for a in {a..z}; do for b in {a..z}; do for c in {a..z}; do printf "@%s%s%s%s%s\n" $a $b $c $c $c; done; done; done > logins.txt
```



```bash
for a in {a..z}; do for b in {a..z}; do for c in {a..z}; do for d in {a..z}; do printf "@tg%s%s%s%s\n" $a $b $c $d; done; done; done; done > logins.txt
```