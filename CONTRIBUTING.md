# Contributing to iofree

We welcome contributions to `iofree`! To ensure a smooth and effective collaboration, please follow these guidelines.

## How to Contribute

1.  **Fork the Repository:** Start by forking the `iofree` repository to your GitHub account.
2.  **Clone Your Fork:** Clone your forked repository to your local machine:
    ```bash
    git clone https://github.com/your-username/iofree.git
    cd iofree
    ```
3.  **Create a Virtual Environment:** It's highly recommended to work within a virtual environment:
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
    ```
4.  **Install Dependencies:** Install the project dependencies in editable mode:
    ```bash
    pip install -e .[dev]
    ```
5.  **Create a New Branch:** Create a new branch for your feature or bug fix:
    ```bash
    git checkout -b feature/your-feature-name
    # or
    git checkout -b bugfix/your-bug-fix-name
    ```
6.  **Make Your Changes:** Implement your feature or fix the bug. Ensure your code adheres to the existing style and conventions.
7.  **Write Tests:** Add appropriate unit tests for your changes. Ensure all existing tests pass and your new tests cover the added functionality or fix.
    ```bash
    uv run pytest
    ```
8.  **Run Linters and Formatters:** Ensure your code is formatted correctly and passes linting checks:
    ```bash
    uv run ruff check .
    uv run ruff format .
    ```
9.  **Commit Your Changes:** Write clear and concise commit messages. A good commit message explains *what* was changed and *why*.
    ```bash
    git commit -m "feat: Add new feature X" # or "fix: Fix bug Y"
    ```
10. **Push to Your Fork:** Push your branch to your forked repository:
    ```bash
    git push origin feature/your-feature-name
    ```
11. **Open a Pull Request:** Go to the original `iofree` repository on GitHub and open a pull request from your forked branch. Provide a detailed description of your changes.

## Code Style

`iofree` follows [PEP 8](https://www.python.org/dev/peps/pep-0008/) for code style. We use `ruff` for linting and formatting. Please ensure your code passes these checks before submitting a pull request.

## Reporting Bugs

If you find a bug, please open an issue on the [GitHub issue tracker](https://github.com/guyingbo/iofree/issues). Provide a clear description of the bug, steps to reproduce it, and expected behavior.

## Feature Requests

If you have an idea for a new feature, please open an issue on the [GitHub issue tracker](https://github.com/guyingbo/iofree/issues) to discuss it. This helps ensure that the feature aligns with the project's goals and avoids duplicate effort.

Thank you for contributing to `iofree`!