# dockerized python api for the he853 usb stick

Had this lying around. I use this for controlling some lights using Node-red for over a year. Has not failed me yet.

It uses the application and library for the Home Easy he853 from https://github.com/hphde/he853-cli.
For more explanation on the parameters available in the api, look at the readme for the he853-cli or call the api with ```/help```.

Call ```/status``` for status and to see if the stick is there.
And ```/switch``` with parameters 

Example: ```http://he853api:8000/switch?address=1001&action=on```

```action``` can be either on or off or a number of 3 digits for a dimmer. 

## 'Works for me', so use at your own risk.

I do some parameter evaluation to make sure the api is safe to use. It does do a call to an external application so access to the underlying operationg system is possible in theory.

See the docker-compose.yml

I guess it is as safe as the python fastapi module and he853-cli 

Just do a ```docker-compose build``` and ```docker-compose up``` to build and run. 

The code is so simple that it might be self explanatory.

## Update: major rewrite by lumo

Since I had to rebuild the docker server this was running on I thought it would be interesting to have the api server analyzed an refactored by Lumo. Lumo is a privacy respecting AI solution from Proton.

I agreed with it's conclusions about my code and setup and it's proposal to refactor and improve the code. 

So now there is an API key to protect access. Some deprecated python code was replaced. And it has been written even more secure and dependable. Not all went perfect. But that is why there still is a human-in-the-loop.