# mydig-webservice

## Components

- Rest service (Flask app)
- Git synchronizer (local daemon process)

## Rest service

All the input and output are formatted in json, please set `Content-Type` to `application/json` in header.

## Sync command

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
