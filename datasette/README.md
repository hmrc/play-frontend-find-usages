# Datasette

This folder contains some helpful additions and configuration for datasette to make it easier to use with the output of the `find-usages` tool. You can start datasette with these changes you can run (from the parent directory):

```
$ datasette path/to/usages.db --open --plugins-dir ./datasette/plugins --metadata ./datasette/metadata.yml --static static:./datasette/static/ --memory
```

![datasette/example.png](example.png)