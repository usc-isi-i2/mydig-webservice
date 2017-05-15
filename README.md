# mydig-webservice

## Components

- Rest service (Flask app)
- IO Handler (local daemon process)
	- command parser
	- git controller
	- file system controller

## IO handler command

Format in json:

```
{
	"command": ...,
	...
}
```

general return format:

```
{
	"return_code": 0 (success) / 1+ (fail),
	"data": "object or string when return code is 0",
	"error_message": "error message when return code is a positive integer"
}
```

### git push

async, push to remote repo, exception should be raised for conflict

```
{
	"command": "push"
}
```

### git pull

sync, needs to return json data, only used for initialization.

```
{
	"command": "pull"
}
```

### save

async, write content to file, add and commit locally

```
{
	"command": "save",
	"data": {
		...
	}
}
```
