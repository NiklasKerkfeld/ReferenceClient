# LLM bases reference extraction


## Make it run
### .env
To send requests to the API you need to add a .env file to the main folder with your access token.
This should look like this:
```.env
TOKEN=<YOUR-ACCESS-TOKEN>
```

### config
Set up the config file as you need it:
```yaml
server: address of the server
model: the model you want to use
prompt: path to the prompt .txt file
input: folder with the pdfs
output: folder where the results are saved
timeout: time until file upload is canceled
```
You can also set variable on specific runs by given them as hyperparameter like this:
```terminaloutput
python main.py output=path/to/folder
```


## Preprocessing
Unfortunately a lot of files are not comatible with the Gesis API as they are. 
The solution I found is to open it once in LibreOffice Draw and export it again as pdf.
I could automate this process using the preprocessing script. 
```terminaloutput
python preprocess.py
```

## Run
The main program can now be simply run by calling:
```terminaloutput
python main.py
```
The program produces multiple outputs in the given `output` folder. 
First it saves all pain responses message as .txt files in the `message` folder.
Then it extracts the xml-part from the response. This is saved in the `xml` folder.
Lastly all references found are added to the `output.csv`.


## Prompt
The prompt can be found in the `prompts/prompt.txt file. 
You can also have multiple prompt files and select the one used in the config file or by a given parameter.
