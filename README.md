# github
A [Mythic](https://github.com/its-a-feature/Mythic) C2 Profile that allows agents to perform comand and control (C2) communication over GitHub issue comments.

:warning: I get it... Reading is hard. 
However, setting up this C2 profile is a bit tedious with numerous required steps. 
Please read the Setup steps in the documentation located at `https://<your-mythic-server>:7443/docs/c2-profiles/github` after installing the C2 Profile. 
You can do it, I believe in you...

## Installation
To install this C2 profile on your Mythic server, log into your Mythic server's command line and run the following command:  
```
sudo ./mythic-cli install github https://github.com/scottctaylor12/github
```

## Setup
Read the warning at the top of the README!

## Compatable Agents
At this time, the following agents can use the GitHub C2 Profile:
* Athena

## Development
I'm happy to have a look at code contributions! 
Please contribute to the `dev` branch at https://github.com/scottctaylor12/github :)

The C2 server code is written in Python and located in `C2_Profiles/github/github/c2_code`