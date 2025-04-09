# AWS_Examples

> [!NOTE]
> Repository for AWS related tasks.


## Fibo AWS

Fibo AWS is a simple lambda function which takes a value of a parameter from URL and calculates Fibonacci sequence based on that number. If the parameter is not provided or the value of a parameter is not correct type, the function returns an errror message.

### URL


The url to the fibo lambda function: [Fibo lambda URL](https://n1x1vcs75d.execute-api.eu-north-1.amazonaws.com/fibo-function)


### Payload

The payload for the url is a **GET** request and the parameter is **number**, the function only accepts this parameter. 
Parameter must be an integer.
For example:  number=9
Example payload: [Fibo lambda example](https://n1x1vcs75d.execute-api.eu-north-1.amazonaws.com/fibo-function?number=9)


### Respone

Response of the lamba function comes back in a json format if it was successful, which only has one key and value.
The key is **result** and the value is the number that is returned from a function of a given **number** parameter.
Example of successful response: **{"result": 34}**
In case the request was unsuccessful, the function return a string, which contains an error message on what may went wrong.
Example of unsuccessful response: **Please enter a number or correct parameter is 'number'**
