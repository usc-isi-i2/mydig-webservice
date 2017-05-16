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

sync, needs to return once finished, only used for initialization.

```
{
	"command": "pull"
}
```

### save

async,add and commit locally

```
{
	"command": "commit",
	"files": ["file1", "dir1/file2"],
	"message": "commit message, optional"
}
```
