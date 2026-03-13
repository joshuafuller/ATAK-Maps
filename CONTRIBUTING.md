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

Before submitting a pull request, use the helper scripts in `scripts/` to catch problems early. All three require Python and the `mapvalidator` package in this repository.

* **`./scripts/validate.sh`** — Runs deep deterministic validation on every XML map file (zoom ranges, URL placeholders, casing, serverParts, and more). No network access needed, so it runs fast. Pass `--strict` to treat warnings as errors (this is what CI does).

* **`./scripts/test-map.sh <file>`** — Validates and probes a single map file. Use this when you're adding or editing one map:
  ```bash
  ./scripts/test-map.sh Google/google_hybrid.xml
  ```

* **`./scripts/probe.sh`** — Validates all maps and probes every tile server for liveness. This makes network requests, so it takes longer. Useful for a final check before opening your PR.

CI will run schema validation automatically on every pull request, but running these locally first saves time and review cycles.

## Contact

If you have any questions or issues, feel free to contact us.

Thank you for your contributions!
