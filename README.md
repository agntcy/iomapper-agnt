# IO-Mapper Agent

[![Contributor-Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.1-fbab2c.svg)](https://github.com/agntcy/acp-sdk/blob/main/CODE_OF_CONDUCT.md)

## About The Project

When connecting agents in an application, the output of one agent needs to be compatible with the input of the following agent. This compatibility needs to be guaranteed at three different levels:

1. transport level: the two agents need to use the same transport protocol.
2. format level: the two agents need to carry information using the same format (e.g. same JSON data structures)
3. semantic level: the two agents need to “talk about the same thing”.

Communication between agents is not possible if there are discrepancies between the agents at any of the layers [1-3].

Ensuring that agents are semantically compatible, i.e., the output of the one agent contains the information needed
by later agents, is an problem of composition or planning in the application. This project, the IO Mapper Agent,
addresses level 2 and 3 compatibility. It is a component, implemented as an agent, that can make use of an LLM
to transform the output of one agent to become compatible to the input of another agent. Note that this may mean
many different things, for example:

- JSON structure transcoding: A JSON dictionary needs to be remapped into another JSON dictionary
- Text summarisation: A text needs to be summarised or some information needs to be removed
- Text translation: A text needs to be translated from one language to another
- Text manipulation: Part of the information of one text needs to be reformulated into another text
- Any combination of the above

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

Learn how to use our different Mappers
[USAGE.md](https://agntcy.github.io/iomapper-agnt/#_usage.md)

## Contributing

Contributions are what make the open source community such an amazing place to
learn, inspire, and create. Any contributions you make are **greatly
appreciated**. For detailed contributing guidelines, please see
[CONTRIBUTING.md](https://github.com/agntcy/acp-sdk/blob/main/docs/CONTRIBUTING.md)

## Copyright Notice and License

[Copyright Notice and License](https://github.com/agntcy/acp-sdk/blob/main/LICENSE)

Copyright (c) 2025 Cisco and/or its affiliates.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
