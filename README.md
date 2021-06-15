# cmif-moritz

## About

This repository contains the CMIF-encoded ([Correspondence Metadata Interchange Format](https://github.com/TEI-Correspondence-SIG/CMIF)) digital correspondence list (*letters.xml*) of the editions of "[Edition der Briefe Philipp Jakob Speners (1635–1705) vor allem aus der Berliner Zeit (1691–1705)](https://www.saw-leipzig.de/de/projekte/edition-der-briefe-philipp-jakob-speners)", a running research project of the [Saxon Academy of Sciences and Humanities in Leipzig](https://www.saw-leipzig.de).

The CMIF-XML was generated from a table of letters (*letters.csv*) with the [csv2cmi webapp](https://cmif.saw-leipzig.de/), which gives easy and web based access to the tool [csv2cmi](https://github.com/saw-leipzig/csv2cmi). According (bibliographic) metadata is in *csv2cmi.ini*. For management of authority identifiers (GND, Geonames) for named entities (persons, places, organisations) within the CSV we used the tool [ba[sic?]](https://github.com/saw-leipzig/basic.app).

Letters metadata are harvested by the webservice [correspSearch](https://correspsearch.net/) and can be browsed, searched and received via browser or [REST-API](https://correspsearch.net/index.xql?id=api&l=en).

## Issues

If you find any mistakes, let us know, by creating an issue.

## Contributors

* Marcus Heydecke
* Uwe Kretschmer
* Klaus vom Orde
* Lars Scheideler
* Marius Jörg Stachowski

## License

This work is licensed under a
Creative Commons Attribution 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by/4.0/>.
