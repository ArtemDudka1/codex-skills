# Personal Codex Skills

Личные скиллы и инструменты ArtemDudka1 для Codex.

## Codex Arena

[Скилл](skills/codex-arena/SKILL.md) · [Подробная инструкция](skills/codex-arena/README.md)

32 независимых аудитора → отбор планов до восьми → отдельные worktrees с
исправлениями → cross-review и внешние проверки → итоговая ветка и diff.
Состояние сохраняется на диске; завершённые модельные задания не повторяются.

### Установка скилла

Нужны Python 3.11+, Git и авторизованный Codex CLI. Из корня клона:

```sh
mkdir -p ~/.agents/skills
ln -s "$(pwd)/skills/codex-arena" ~/.agents/skills/codex-arena
```

Если путь уже существует, сначала проверьте его — не перезаписывайте чужой скилл.
Codex обнаруживает новые скиллы; если не появился, откройте новый чат или перезапустите приложение.

### Запуск из чата

Откройте нужный локальный проект в Codex и выберите Codex Arena в списке скиллов
либо упомяните `$codex-arena`:

> Используй $codex-arena для глубокого аудита и улучшения текущего проекта.
> 32 агента. Работай в отдельных ветках, проверь реальные пользовательские
> сценарии и оставь итоговую ветку с diff для моего просмотра.

Codex прочитает проект, подготовит применимые команды проверок и запустит CLI.
Это реальный турнир с расходованием лимита. Для подготовки без запуска напишите
«подготовь конфигурацию и план, турнир пока не запускай».

### Прямой CLI

```sh
python3 skills/codex-arena/bin/codex-arena --help
python3 skills/codex-arena/bin/codex-arena plan /path/to/project --agents 32
```

Профиль модели/проверок нужен для реального run; см. подробную инструкцию.
Проверки ядра используют fake Codex executable; реальные модели и AI Factory ещё
не проходили полноценный pilot. Нельзя считать тестовый турнир доказательством
реальной квоты или production-ready статуса.

## Структура

Каждый новый скилл размещается отдельной папкой `skills/<name>/` с `SKILL.md`
и необходимыми ресурсами. Личные токены, состояния прогонов, проектные данные,
worktrees и файлы авторизации сюда не добавляются.

## Reels Team

[Skill](skills/reels-team/SKILL.md) · [Team rules](skills/reels-team/AGENTS.md) · [Quality criteria](skills/reels-team/quality/criteria.md)

A coordinator delegates to a designer, scriptwriter, code-based editor, sound director and independent reviewer. Includes frozen acceptance criteria and bounded repair cycles. Documentation and handoffs are English; all user-facing chat is Russian. Internal reasoning may use English without being disclosed.

Install from a persistent clone:

```sh
mkdir -p ~/.agents/skills
ln -s "$(pwd)/skills/reels-team" ~/.agents/skills/reels-team
```

Inspect an existing destination before installation; never overwrite it blindly. Open a new Codex chat if skill discovery needs refreshing. Invoke `$reels-team` with a topic, available assets and desired duration. The host must provide delegation and appropriate media tools; files alone do not start agents. This package has not yet completed an end-to-end Reel production pilot.
