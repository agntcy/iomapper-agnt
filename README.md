# IO-Mapper Agent

[![Release](https://img.shields.io/github/v/release/agntcy/iomapper-agnt?display_name=tag)](CHANGELOG.md)
[![Lint](https://github.com/agntcy/iomapper-agnt/actions/workflows/lint.yml/badge.svg?branch=main)](https://github.com/marketplace/actions/super-linter)
[![Contributor-Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.1-fbab2c.svg)](CODE_OF_CONDUCT.md)

## About The Project

When connecting agents in an application, the output of one agent needs to be compatible with the input of the following agent. This compatibility needs to be guaranteed at three different levels:

  1. transport level: the two agents need to use the same transport protocol. 
  2. format level: the two agents need to carry information using the same format (e.g. same JSON data structures)
  3. semantic level: the two agents need to “talk about the same thing”.

Communication between agents is not possible if there are discrepancies between the agents at any of the layers [1-3].   

Ensuring that agents are semantically compatible, i.e., the output of the one agent contains the information needed by later agents, is an problem of composition or planning in the application. This project, the IO Mapper Agent, addresses level 2 and 3 compatibility.  It is a component, implemented as an agent, that can make use of an LLM to transform the output of one agent to become compatible to the input of another agent. Note that this may mean many different things, for example:

  * JSON structure transcoding: A JSON dictionary needs to be remapped into another JSON dictionary
  * Text summarisation: A  text needs to be summarised or some information needs to be removed
  * Text translation: A text needs to be translated from one language to another
  * Text manipulation: Part of the information of one text needs to be reformulated into another text
  * Any combination of the above

The IO mapper Agent can be fed the schema definitions of inputs and outputs as defined by the [Agent Connect Protocol](https://github.com/agntcy/acp-spec).

## Getting Started

To get a local copy up and running follow these simple steps.

### Prerequisites

### Installation

1. Clone the repository

   ```sh
   git clone https://github.com/agntcy/iomapper-agnt.git
   ```

## Usage

## Roadmap

See the [open issues](https://github.com/agntcy/iomapper-agnt/issues) for a list
of proposed features (and known issues).

## Contributing

Contributions are what make the open source community such an amazing place to
learn, inspire, and create. Any contributions you make are **greatly
appreciated**. For detailed contributing guidelines, please see
[CONTRIBUTING.md](CONTRIBUTING.md)

### Top contributors

<a href="https://github.com/agntcy/iomapper-agnt/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=agntcy/iomapper-agnt" alt="contrib.rocks image" />
</a>

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## License

Distributed under the Apache-2.0 License. See [LICENSE](LICENSE) for more
information.

## Contact

Project Link:
[https://github.com/agntcy/iomapper-agnt](https://github.com/agntcy/iomapper-agnt)
