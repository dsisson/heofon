# heofon

## What is Heofon?
_Heofon_ is Old English for the sky or the heavens. 

Heofon is a test automation framework shell written in Python and using the pytest test runner, and using Playwright instead of Selenium for browser automation.

Heofon is designed to support functional testing for one or more apps in an ecosystem, as well as end-to-end testing across these apps.

Heofon provides a basic starting point for building a custom test framework; you add the test data models, custom application wrappers, and the tests. Heofon is intended as a teaching tool for beginning test automators; Heofon is NOT a general test framework or test tool.


## What Heofon is Not
Heofon is not a test framework, because
+ it doesn't have a body of tests beyond simple demonstration examples;
+ it doesn't have any application models or wrappers.

Heofon is a scaffolding on which a custom test automation framework can be built. Heofon does have:
+ the Pytest test runner (in my opinion the best one available, and certainly the best for Python)
+ an advanced data collection and logging system
+ utilities that I find useful in supporting and extending test activities
+ integration with Playwright
+ example tests that demonstrate how to use the framework-to-be.

Heofon is not a turn-key tool; you will need to modify Heofon to make it useful for your test needs.


## Installing Heofon
Heofon is intended to be a starting point for your automation code framework, so while there is a range of ways the code could be packaged and distributed cleanly, just fork this project and set it up locally.

What I do is:
+ think up a cool name for the test automation framework I'm __going__ to build
+ clone the code to a local repo
+ set up a virtualenv
+ run requirements.txt
+ add mappings to the local heofon project in my bash profile
+ create a new repo on GitHub for the new framework (Heofon has done its job)

You will need to create the following directory in your home folder: ````~/dev````

Create a virtualenv in the directory ````~/dev/venv````. Don't activate that yet.

On a Mac, you'll probably have to add mappings in your bash profile to the project:

````
export PATH=$PATH:~/dev/venv
export PATH=$PATH:~/dev/heofon
export PYTHONPATH=$PYTHONPATH:~/dev/heofon
````

Activate the virtualenv ~/dev/venv.


## Running Heofon
Heofon is typically run from the command line. Pytest handles test collection and the reporting of errors.

### Base Command
The base command to collect and run tests with pytest is the following:
````
$ cd <path_to_heofon>
# you should be in the top-level heofon folder
$ pytest heofon/tests
````

### Controlling The Collected Tests
Pytest supports several ways to control test collection.

1. string matches in the name path for the test methods
````
# collect and run every test with the string "example" in filename, classname, method name
$ pytest heofon/tests -k example
````

2. marker matches for test classes or methods
````
# collect and run every test class or test method marked with the pytest.marker "example"
$ pytest heofon/tests -m example
````

3. combined marker matches AND string matches
````
# collect and run every test marked with the pytest.marker "example" AND containing the string "simple"
$ pytest heofon/tests -m example -k simple
````


### Collecting Tests Without Running Them
Sometimes you'll need to collect but not run tests:
````
# collect every test marked with the pytest.marker "example" AND containing the string "simple"
$ pytest heofon/tests -m example -k simple --collect-only
collected 7 items
<Module 'examples/test_examples.py'>
  <Class 'ExampleTests'>
    <Instance '()'>
      <Function 'test_simple_pass'>
      <Function 'test_simple_fail'>
````


### Killing a Test Run
To stop a test run, hit CTRL + C.


### Command Line Arguments
Optional command line arguments you can pass to heofon:
+ *tier* is the environment to run the tests against; the choices are 'local',
'qa', 'staging'; defaults to 'qa'. These don't work out of the box; they are placeholders
that need to be configured with the actual name and URLs.
+ *browser* is the browser to run the tests in; the choices are 'chromium', 'firefox'; defaults to 'chromium'.
+ *headed* is a flag to run the browser in headed mode; the choices are 'on' and 'off'; defaults to 'off'.
+ *tracing* is a flag to enable Playwright tracing; the choices are 'on' and 'off'; defaults to 'off'.


### Logging
Heofon is intended to be verbose in its logging; however, that's up to you to implement as you build out your own framework.

By default, Heofon creates an output folder at heofon/output, and then for each test run Heofon creates a folder in _output_ named with the testrun's timestamp; this folder gets the HTML test results page, plus the text log of test run activity. This output is not automatically cleaned up. You'll have to define a workflow for this, if you want.


### Tracing and Viewing Traces
Tracing can be enabled by passing the --tracing=on flag to the pytest command. The trace file is saved to the output folder for the test run's test case. 

To invoke the Pytest run command with tracing enabled, use the following command:

```
$ pytest heofon/tests --tracing=on
```

To view the trace, use the following command:

```
$ playwright show-trace <path_to_trace>
```


### Recording and Viewing Videos
Video recording can be enabled by passing the --video=on flag to the pytest command. The video file is saved to the output folder for the test run's test case. 

To invoke the Pytest run command with tracing enabled, use the following command:

```
$ pytest heofon/tests --video=on
```

To view the video, open it from the output/testrun/testcase folder on local filesystem.

