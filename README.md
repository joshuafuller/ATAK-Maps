# ATAK-Maps

![ATAK-Maps Logo](https://github.com/joshuafuller/ATAK-Maps/blob/master/images/ATAK_MAPS_Logo.png?raw=true)

![GitHub tag (latest by date)](https://img.shields.io/github/v/tag/joshuafuller/ATAK-Maps) ![GitHub Release Date](https://img.shields.io/github/release-date/joshuafuller/ATAK-Maps?style=flat) ![GitHub All Releases](https://img.shields.io/github/downloads/joshuafuller/ATAK-Maps/total?style=flat) [![Discord](https://img.shields.io/discord/698067185515495436?style=flat)](https://discord.gg/dQUYADMW87) [![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/joshuafuller/ATAK-Maps)

## Detailed Overview of ATAK-Maps

ATAK-Maps is a comprehensive collection of XML files, formatted in the Mobile Atlas Creator (MOBAC) format. This format is used in [Android Tactical Assault Kit (ATAK)](https://tak.gov), an advanced geospatial mapping tool employed in various sectors including military, law enforcement, and emergency services. This repository and its contents are not affiliated with TAK.GOV in any way.

### What are ATAK-Maps?

These XML files in ATAK-Maps act as pointers or references to a multitude of online map sources. By using these files, ATAK can seamlessly access and display current and relevant map imagery from these sources. This capability is vital for operations requiring up-to-date geospatial information.

### MOBAC Format

The MOBAC format is integral to the functionality of ATAK-Maps. It enables the definition of how ATAK accesses these online map sources. For more detailed information on the MOBAC format, visit [Mobile Atlas Creator](https://mobac.sourceforge.io/).

### Usage and Functionality

- **Dynamic Map Access**: ATAK-Maps facilitates the dynamic access of various map sources, ensuring that users have the most current imagery available for their operational needs.
- **Offline Caching**: One of the key features of ATAK is its ability to cache these maps. With ATAK-Maps, users can download and store map areas for offline use, which is crucial in environments with limited or no internet access.
- **Customization and Selection**: Users can also select specific areas and set the desired image quality for downloads, allowing for tailored map coverage based on operational requirements.

## Installation Guide

To integrate ATAK-Maps into your ATAK application, follow these steps:

1. **Download**: Get `ATAK-Maps.zip` from the [Releases page](https://github.com/joshuafuller/ATAK-Maps/releases).
2. **Locate**: Navigate to 'Downloads' in your file manager.
3. **Extract**: Open `ATAK-Maps.zip` and extract its contents.
4. **Transfer**: Move the map files (anything not prefixed `grg_`) to the `ATAK/imagery` directory and the overlays (anything prefixed `grg_`) into the `ATAK/grg` directory.
5. **Verify**: In ATAK, ensure the new maps appear in the map list and the overlays appear in the overlay list.

## Frequently Asked Questions (FAQ)

- **Can I cache these maps for offline use?** Yes, ATAK supports automatic and manual caching of maps.
- **Will more maps be added?** We continuously update our map collection. Share your suggestions [here](https://github.com/joshuafuller/ATAK-Maps/issues).

## Open Street Maps Compatibility

Please note that Open Street Maps may restrict ATAK client access. These maps are included for reference, and we're exploring solutions.

## Contributing

We welcome your contributions! Review our [contribution guidelines](CONTRIBUTING.md) for more information.

## Support

Join our [Discord server](https://discord.gg/dQUYADMW87) for support and community engagement.

## License

ATAK-Maps is distributed under the [MIT License](LICENSE).
                        
## Stargazers over time
[![Stargazers over time](https://starchart.cc/joshuafuller/ATAK-Maps.svg?variant=adaptive)](https://starchart.cc/joshuafuller/ATAK-Maps)

                    
