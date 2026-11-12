# SC-DOC

Сайт документации языка SC: https://winchestersdc79-hub.github.io/SC-DOC/

`index.html` собирается из спецификации компилятора `docs/spec.md`
(репозиторий [sviroxk/sviroxk-compiler](https://github.com/sviroxk/sviroxk-compiler))
и руками не правится. Каждый пример спецификации компилирует и запускает
`tests/spec-examples.sh` компилятора, поэтому примеры на сайте рабочие.

Обновить страницу после изменения спецификации:

```bash
python3 gen.py ../sviroxk-compiler/docs/spec.md > index.html
```

Нужен только Python 3. Публикация — GitHub Pages из ветки `main`.
