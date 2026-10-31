# Contributing to ATAK Maps

First off, thank you for considering contributing to ATAK Maps! It's contributors like you that make ATAK Maps such a valuable resource. We welcome and appreciate contributions from the community!

## Prerequisites

Before you begin, ensure you have met the following requirements:

* You have a [GitHub](https://github.com/) account.
* You have installed the [Git](https://git-scm.com/) on your local machine.

## Contributing Map Files

To contribute to ATAK Maps, follow these steps:

1. Fork the repository.
2. Clone the forked repository to your local machine.
3. Create a new branch for your map files.
4. Add your map files to the new branch.
5. Commit your changes, ensuring you follow our commit message guidelines.
6. Push your changes to your forked repository.
7. Submit a pull request to our repository.

## Guidelines for Map Files

* Ensure your map files are in the correct format.
* Make sure your map files do not contain any sensitive or proprietary information.
* Verify that your map files are accurate and up-to-date.

## Testing Your Changes

Maps live in `maps/base/<source>/` (base maps) and `maps/overlays/` (transparent overlays, `grg_` prefix). Full guide: [Add a map](https://joshuafuller.github.io/ATAK-Maps/creating-custom-maps/). Before you open a pull request, run these with [uv](https://docs.astral.sh/uv/):

* **Test your map the way ATAK loads it** (fetches real tiles with ATAK's URL rules and user agent):

  ```bash
  uv run python -m mapvalidator --harness . --only maps/base/google/google_hybrid.xml
  ```

* **Check every map's XML** (zoom ranges, URL placeholders, serverParts and more; no network):

  ```bash
  uv run python -m mapvalidator
  ```

* **Run the tests** if you change Python code:

  ```bash
  uv run --extra dev pytest
  ```

CI runs all of these, the schema check and a browser check of the site on every pull request.

## Contact

If you have any questions or issues, feel free to contact us.

Thank you for your contributions!
