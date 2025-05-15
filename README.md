# Code Review To Communication Network

Data collection pipeline for the study "The Upper Bound of Information Diffusion in Code Review"

## Introduction

With this repository, we share a software tool to extract code review interactions from Gerrit and GitHub and generate communication networks from the extracted data. These communication networks networks represent the interactions between developers during the code review process.

Since identifying bots requires some manual effort, we provide a Jupyter notebook (`main.ipynb`) that thoroughly documents the process and offers flexibility to experiment and adjust configurations as needed.

## Installation and Requirements

```bash
pip3 install -r requirements.txt
```

To crawl GitHub, you'll need a [GitHub access token for authentication](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens).

## Usage

Run `main.ipynb` in your prefered Jupyter environment (for example, Visual Studio Code).

## License

Copyright © 2025 Michael Dorner

This work is licensed under [MIT license](LICENSE).
