# github
A Mythic C2 Profile that performs C2 comms over GitHub issue comments.

:warning: I get it... Reading is hard. 
However, setting up this C2 profile is a bit tedious with numerous required steps. 
Please read the documentation closely located at `https://<your-mythic-server>:7443/docs/c2-profiles/github` (recommended) after installing the C2 Profile. 
You can do it, I believe in you...

## Installation
To install this C2 profile on your Mythic server, log into your Mythic server's command line and run the following command:  
```
sudo ./mythic-cli install github https://github.com/scottctaylor12/github
```

## Setup
Read the warning at the top of the README!

## Development
I'm happy to have a look at code contributions! 
Please contribute to the `dev` branch at https://github.com/scottctaylor12/github :)

The C2 server code is written in Python and located in `C2_Profiles/github/github/c2_code`