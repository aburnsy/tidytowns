# TMB Tidy Towns

Project management and community tracker for Two Mile Borris Tidy Towns, Co. Tipperary.

**Website:** [https://aburnsy.github.io/tidytowns/](https://aburnsy.github.io/tidytowns/)

## About

Two Mile Borris is a Category B village (201-1000 population) competing in the SuperValu Tidy Towns competition. This site tracks our community improvement projects across categories including streetscape, green spaces, nature and biodiversity, sustainability, and more.

## How to Contribute

Visit the website to:

- **Browse projects** - see what we're working on
- **Propose a project** - suggest a new idea for the village
- **Comment on a project** - share feedback on existing work
- **Volunteer** - sign up to help with a project

## For Maintainers

### Build and preview the site

```bash
cd site && uv run --with mkdocs-material mkdocs serve
```

### Add a new project

```bash
bash scripts/new-project.sh
```

### Add a task to a project

```bash
bash scripts/new-task.sh
```

### Rebuild derived pages

```bash
bash scripts/generate-index.sh
bash scripts/generate-my-tasks.sh
```
