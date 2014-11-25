.. sectnum::
.. image:: https://travis-ci.org/jdevera/subdue.png?branch=master
    :target: https://travis-ci.org/jdevera/subdue

**Warning**: This project is currently in a documentation writing phase **before development**.

Subdue: Your Programs Under Control
===================================

sub·due:
    *transitive verb* : to conquer and bring into subjection.

Subdue is a simple framework that enables you to quickly and easily create very powerful shell commands based on subcommands, like *git* or *svn*, that you run like this::

    $ program subcommand [arguments]

In subdue's terminology, such command is called a **sub**, and its subcommands are independent programs that are put together under one common directory. The main command (the **driver**) is responsible for launching those subcommands.

Subdue gives the driver some super powers that can be harnessed with some collaboration from the subcommands themselves. Subcommands can choose to adhere to certain conventions in order to take advantage of these powers. Some of these services are:

 - Shell completion for subcommands
 - Brief usage text extraction
 - Full help extraction and formatting

Although *subdue* itself is written in Python, it is language agnostic when it comes to subcommands. Anything that can be executed can be a subcommand, be it a script, a binary or even a symlink to any of those!

.. contents:: Table of Contents

How to install
--------------

Using ``pip`` (recommended):

.. code::

    $ pip install subdue

Installing from source:

.. code:: bash

    $ git clone https://github.com/jdevera/subdue
    $ cd subdue
    $ python setup.py install

How to create a sub
-------------------

Run this command:

.. code:: bash

    $ subdue create SUB_NAME

This creates a directory called SUB_NAME under the current directory and shows some useful information on what to do next. That directory *is* your sub.

It is possible, for learning purposes, to create an example sub that comes preloaded with a series of dummy subcommands that showcase all the features in Subdue. To create such example sub, run this:

.. code:: bash

    $ subdue create --example SUB_NAME

Setting up a sub
----------------

Once your sub is created, run:

.. code:: bash

    $ SUB_NAME/bin/SUBNAME init

This will show you the steps required to set up the sub. This normally involves adding a call to a special form of ``init`` from one of your shell's startup files. That call generates code for your shell that takes care of adding the directory of the main command to the ``PATH``. It also sets up shell completion and the *eval-command* feature described later in this document.

.. Tip::
    Alternatively, to gain some speed, you can choose to run the provided steps manually once and store their output in the shell startup file. There is, however, a trade-off: If subsequent versions of subdue provide updates to the shell init code, you will not get them.

Anatomy of a sub
----------------

The following directories and files are contained in a *sub*:

``bin/``
    This **optional** directory contains the main script for this *sub*, which has the same name as the *sub*

``commands/``
    This directory contains the scripts or binaries (anything that can be executed) that will be exposed as subcommands of the *sub*. It can also contain other directories, which will be considered as **subcommand containers**.

``lib/``
    This directory holds helper scripts or binaries that are used by the subcommands in the sub, but are however not exposed as subcommands themselves.  It is added to the ``PATH`` in the environment under which subcommands are run.

``share/``
    User location for files that are not executable. An environment variable exposes this location to the subcommands.


Adding subcommands
------------------

Simple copy or symlink some executable file into the ``commands`` directory of your sub and it will be considered a subcommand. For example, symlinking ``/bin/ls`` to ``commands/sl`` will allow you to run::

    $ SUB_NAME sl
    info.txt sl

If you add a directory under ``commands``, it will be considered a subcommand container. You can have more scripts inside. For example, creating a directory called ``foo`` under ``commands`` and then symlinking ``/bin/date`` to ``commands/foo/date`` will allow you to run::

    $ SUB_NAME foo date
    Fri Oct 18 18:26:13 IST 2013

But it doesn't stop there, you can have nested subcommand containers by creating a directory hierarchy inside a container, thus creating sub sub sub (...) commands :)

Non-executable files in the commands directory or any nested subcommand containers are ignored.

Of course, you can also create a subcommand which is simply a symlink to another subcommand, anywhere in the hierarchy. This is how you can create **aliases** within your sub.


The sub driver
--------------

The default sub driver generated contains only three lines:

.. code:: python

    #!/usr/bin/env python
    from subdue.sub import main
    main()

This assumes the script lives in the ``bin`` subdirectory inside the sub's directory. However, this is not compulsory, any path can be passed to the ``main`` function using the keyword argument ``sub_path`` and then the driver will look for all the expected sub contents to be under that path.

For example, we might have a sub driver called ``foo`` under ``/usr/local/bin/foo`` but store the sub contents under ``/usr/local/lib/subs/foo``. These would be the contents of ``foo``:

.. code:: python

    #!/usr/bin/env python
    from subdue.sub import main
    main(sub_path='/usr/local/lib/subs/foo')


What the framework provides
---------------------------

On top of simply running subcommands through a driver, the Subdue framework provides a lot more extra value to subcommands:

- Certain directories in the path (the one where the driver is and ``lib``)
- Completion for subcommands (if commands declare that they provide it)
- Usage text extraction (if commands adhere to the expected format)
- Help text extraction (if commands adhere to expected format)
- Option to execute commands directly in the running shell (eval-commands)
- General information to subcommands through environment variables
- Some default subcommands, like init or help, that you don't have to implement
- A library of some useful tools to use in subcommands if you happen to be
  writing them in bash or python.

All those will now be covered, all the examples assume an example sub called *exa* has been created and that the current directory is inside the sub:

.. code:: bash

    $ subdue create --example exa
    $ cd exa

The path available to subcommands
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Subcommands receive the same ``$PATH`` as the calling shell, but augmented by Subdue with two additional directories.

First is the directory where the driver is.  This directory is added to the start of the ``$PATH`` and is intended to allow subcommands call other subcommands.

Second is the ``lib/`` directory inside the sub. This is so that helper programs that are stored there can be called directly from subcommands. The programs under ``lib`` are however not exposed as subcommands.

Usage, Summaries, and Help Text extraction
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A subcommand can include a series of special comments that communicate things to Subdue. The main use of this is for help generation. This section explains how to provide the framework with information about the sub itself and its subcommands. Help generation will be explained in the following section.

Help generation uses three different types of comments, for three different levels of detail. This approach brings the nice side effect that scripts will be well documented in their source.

Usage
:::::

The usage string is a single line outlining the allowed parameters for a command

Usage is extracted from a line that starts with::

    # Usage:

Note that any space before or after the hash is not considered, but the comment hash must be the first non-space character in the line in order to qualify as usage indicator.

Whatever follows in the same line, after removing leading and trailing spaces is regarded as the usage string for the subcommand.

For instance, the subcommand ``foo`` in the example sub contains the following line::

    # Usage: exa foo [-e] [-o file]

Which means the usage string for ``foo`` is::

    exa foo [-e] [-o file]

The ``Usage`` directive must appear within the first 100 lines of a subcommand.

Summary:
::::::::

The summary is a single line that briefly explains what the subcommand does. It follows the same convention as for the usage string, but the keyword is ``Summary``. For instance, the ``foo`` subcommand in the example sub has the following line in its source::

    # Summary: Foo all foos

Which means the summary for ``foo`` is::

    Foo all foos

The ``Summary`` directive must appear within the first 100 lines of a subcommand.

Long help text
::::::::::::::

The long help text is a block of text, one or more paragraphs long, that explains in detail everything about the subcommand. Since the text can expand to more than one line, Subdue tries to find the following comment in the source of a subcommand::

    # Help:

And from then on, anything that follows it, for as long as lines **continue to be commented out**, will be regarded as long help text. For instance, again with ``foo``, this is an excerpt of its contents::

    # Help:
    # Foo all available foos and wait for all to be fooed.
    #
    # Options:
    #    -e       Only foo the even foos
    #    -o FILE  Write results to FILE
    #
    # Known Issues:
    # Foos that are fooed in December get reverted back to unfooed state in January

    # This comment is not part of the help text, since there was an
    # interruption in the comment flow.

All trailing spaces, leading spaces and comment hashes are removed and the result is regarded as the long help text.

.. Note::
    Although the full help text might extend beyond the 100th line, the initial ``Help`` directive must be within the first 100 lines of the subcommand file.

Documentation for subcommand containers
:::::::::::::::::::::::::::::::::::::::

Subcommand containers are directories and as such, cannot follow any of the comment convention outlined above. To circumvent this, Subdue reads all the documentation for subcommand containers from a file called ``doc.txt`` that sits directly under the container.

The same conventions outlined above apply. However, since a subcommand container cannot contain options, its usage, if not specified in the file ``doc.txt``, will be generalised as::

    exa baz <command> [<args>]

Where ``exa`` is the sub's name and ``baz`` is the container.

There can also be a ``doc.txt`` file directly under the ``commands/`` directory of a sub. In that case, only the ``Help`` directive is supported and anything in the long help text will be shown in **all the help screens** in the sub. A small description is the recommended contents for this file. In the example sub, this file contains::

    # Help:
    # ===============================================================================
    #        _____                                _         ____          _     
    #       | ____|__  __ __ _  _ __ ___   _ __  | |  ___  / ___|  _   _ | |__  
    #       |  _|  \ \/ // _` || '_ ` _ \ | '_ \ | | / _ \ \___ \ | | | || '_ \ 
    #       | |___  >  <| (_| || | | | | || |_) || ||  __/  ___) || |_| || |_) |
    #       |_____|/_/\_\\__,_||_| |_| |_|| .__/ |_| \___| |____/  \__,_||_.__/ 
    #                                     |_|                                   
    #
    #                                Powered by Subdue
    #                                   Version 0.1
    # ===============================================================================

Variable expansion in extracted documentation
:::::::::::::::::::::::::::::::::::::::::::::

Subdue supports variable expansion in all extracted documentation. By default, only the string ``%COMMAND%`` is expanded to the tokens that form the command, starting with the sub name, followed by all the leading subcommand containers, if any, and ending with the current subcommand name. For instance, a hypothetical subcommand located under ``commands/this/is/an/example`` in the sub called exa would get the string "``%COMMAND%``" replaced with "``exa this is an example``".

This feature is intended to decouple the documentation contents of a subcommand from its location. This will cover the case where a symlink is created to provide an alias, since the help text for alias will then include the name of the alias, rather than the original command.

More of these replacements can be performed by providing the driver's ``main`` with a dictionary as the ``doc_expansions`` parameter. The keys in this dictionary are variable names that, when found in any of the help texts (surrounded by ``%``) will be replaced by:

a) The corresponding value in the dictionary, if it is a string.
b) The result of running the corresponding value, if it is callable.

If the value or the result of the callable has a type other than string, it will simply be converted to string before the expansion.

The callable is given the following arguments:

- The name of the variable
- The name of the sub
- A tuple containing all the tokens that lead up to the current command
- The full path of the sub root directory
- The path of the command, relative to the sub's root
- The number of rows in the current shell
- The number of colunms in the current shell
- A boolean indicating if the subcommand is an *eval-command*

For reference, a callable that mirrors the behaviour of the default ``%COMMAND%`` expansion would be:

.. code:: python

    #!/usr/bin/env python
    from subdue.sub import main

    def COMMAND(_, subname, command_tokens, *args):
        return ((subname,) + command_tokens)

    main(doc_expansions={
        'COMMAND' : COMMAND
        })

.. Caution::
    Although possible, overloading the expansion for ``COMMAND`` can be confusing.

.. TODO: Rething this. Perhaps it's better to provide a help processor that gets the whole string and returns the transformed string.

The built-in *help* subcommand
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

All Subdue subs come packed with a powerful ``help`` subcommand that makes use of all the documentation extracted from subcommands as explained in the previous section.

The ``help`` subcommand can be called with no arguments to provide a top level overview of the whole sub::

    $ exa help
    Usage: exa <command> [<args>]

    ===============================================================================
           _____                                _         ____          _     
          | ____|__  __ __ _  _ __ ___   _ __  | |  ___  / ___|  _   _ | |__  
          |  _|  \ \/ // _` || '_ ` _ \ | '_ \ | | / _ \ \___ \ | | | || '_ \ 
          | |___  >  <| (_| || | | | | || |_) || ||  __/  ___) || |_| || |_) |
          |_____|/_/\_\\__,_||_| |_| |_|| .__/ |_| \___| |____/  \__,_||_.__/ 
                                        |_|                                   

                                   Powered by Subdue
                                      Version 0.1
    ===============================================================================

    These are the available subcommands for exa:
          bar     Raise or lower the bar
       >> baz     Bazinga!
          distim  Make Gostak distim the doshes
          docs    Does a well documented nothing
          foo     Foo all foos
          undoc   --
          

    See 'exa help <command>' for information on a specific command.

This is where each part of this output comes from:

 - The Usage line is automatically generated and it is common for all subs
 - The banner comes from the sub's main ``doc.txt`` under the ``commands/`` directory.
 - The line "These are the available..." is also common for all subs, it precedes a summary of the subcommands.
 - The subcommand summaries, as extracted from the subcommand files. If a subcommand does not provide a summary, a double hyphen ``--`` is shown in place of the summary.
 - The "See 'exa help <command>'..." line is also common for all subs.
    
The help command can alternatively be followed by a subcommand in order to get help for it::

    $ exa help foo
    Usage: exa foo [-e] [-o file]
    
    Foo all available foos and wait for all to be fooed.

    Options:
       -e       Only foo the even foos
       -o FILE  Write results to FILE

    Known Issues:
    Foos that are fooed in December get reverted back to unfooed state in January

In this case, both usage and long help text for the subcommands are presented as extracted, if present.

If help is requested on a subcommand that is not documented, the following is shown::

    $ exa help undoc
    This command isn't documented yet.

The same is shown for commands that don't have an Usage line, regardless of whether they have long help text or not; they are considered *undocumented*. If a subcommand has a usage line but not help text, the summary, if available, will be shown after the Usage.

Note the chevrons (``>>``) before ``baz``. That means baz is a **subcommand container**, rather than a command directly. This means ``baz`` is a directory under ``commands/`` in the sub. Help can be requested for subcommand containers too::

    $ exa help baz
    Usage: exa baz <command> [<args>]

Configuration for the help command
::::::::::::::::::::::::::::::::::

The behaviour of the help command is highly configurable. The following *switches and knobs* are available:

- Override the sub's main ``doc.txt`` with some custom text
- Override the default line that precedes the command summaries
- Override the name of the file where documentation for subcommand containers is stored (by default it is ``doc.txt``)
- Provide a callable to format the summary lines (gets all lines as a list of tuples with (name, summary or None, True if container else False))
- Provide a callable to format the long help text (this can be used to parse some mark-up and could allow writing help text in, for example, Markdown)

.. TODO Design the API for these

The eval-command feature
~~~~~~~~~~~~~~~~~~~~~~~~

With the commands of a sub, there exist the same limitation as with running any other script: The script cannot change the state of the current running shell, e.g., change directories, export environment variables for subsequent commands, etc. When this functionality is needed, one must resort to shell functions or aliases.

Subdue provides a way for subcommands to modify the shell, by turning those commands into something like a shell function. You could do something like::

  $ exa gohome

And have your shell change directories to your home.

When you initialise the sub with the ``init`` built-in subcommand, it registers a shell function with the name of your sub that will relay all calls to the sub driver. However, for some subcommands, it will capture their output and eval it!.

These commands are called **eval commands**. A prefix in the file name of a command (by default ``sh-``) indicates that such command is an eval command. This prefix is not exposed by the driver:

In the example above, ``gohome`` would be a script under ``exa/commands/sh-gohome`` (note the ``sh-`` prefix) which would contain::

    #!/bin/sh
    echo "cd ~"

Running this as::

    $ exa sh-gohome

Would just print ``cd ~`` on your shell. However, when run without the prefix as in the example further up, this shell function finds out that **it had to add the prefix** to find the command and then it will run it and evaluate its output. This information is also available to the command script itself in the form of an environment variable.

.. TODO document this environment variable

The issue of cross shell incompatibility
::::::::::::::::::::::::::::::::::::::::

A limiting factor of the eval commands is that, since they end up being sourced by the shell, what they output might not work if you switch shells. To try to help to mitigate a bit, the sub wrapper will load an environment variable with the name of the shell running the command. This is then available for the subcommand, and it can be used to determine the kind of output it wants to generate, considering it will be evaluated by a particular shell.

The environment of subcommands
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

All subcommands in a sub receive the following information in form of environment variables:

``_SUB_NAME_``
  Contains the name of the sub.

``_SUB_COMMAND_``
  Contains the token of the current command, excluding the arguments.

``_SUB_PATH_COMMAND_``
  Contains the full path to the current command being executed.

``_SUB_PATH_ROOT_``
  Contains the full path to the root of the sub that the command is running on.

``_SUB_PATH_SHARED_``
  Contains the full path to the shared directory in the sub. Even when this can be apparently derived from ``_SUB_PATH_ROOT_``, prefer to use this variable directly.

``_SUB_PATH_LIB_``
  Contains the full path to the lib directory in the sub. Even when this can be apparently derived from ``_SUB_PATH_ROOT_``, prefer to use this variable directly.

``_SUB_IS_EVAL_``
  If the command is being run as an eval command, that is, if the driver had to add the eval command prefix (by default ``-sh``) to the last command token in order to find the script, then this variable has a value of 1. Otherwise it is 0.

``_SUB_SHELL``
  The name of the shell that invoked the driver. This variable is available only when using the functional shell wrapper and it is only meaningful in eval commands.

.. TODO talk about the subdue.script module, which is loaded with the info from environment

Shell Completion
~~~~~~~~~~~~~~~~

Subdue provides shell completion at the driver level out of the box. This means that after it has been set up correctly, a sub can get subcommand names autocompleted in the shell.

But the completion capabilities do not end there. Subdue allows you to easily provide completion also for the parameters of subcommand scripts.

First, Subdue must know whether your script can provide its own completion information. This is achieved by including a line like this in the subcommand script::

    # -*- Provide subdue completion -*-

The ``#`` character is just an example, since it's the one used by many scripting languages to introduce line comments. Subdue will match starting at the first ``-*-`` marker and will make sure that the last ``-*-`` marker appears at the end of the line. Only spaces might appear afterwards.

Of course, if the command is a compiled binary, it's of no use to include such line on its code; Subdue will not be able to determine this from the binary. For such cases, subdue provides an alternative: If your command is called ``foo``, create a file called ``foo.subduecompleter``. The existence of this file lets Subdue know that ``foo`` offers completion.

Once Subdue has determined that the subcommand can generate its own completion information, it will run it with the ``--subdue-complete`` flag to obtain the actual completion information. A script that declares itself a **completion provider** must handle this flag. Anything the script puts out in standard output will be tokenised and used as possible completions.

If the provision of completion information was declared through a ``.subduecompleter`` file, and this file is executable, then this file will be exeuted instead of ``foo`` to generate the completions. However, this one will not receive the ``--subdue-complete`` flag. Thus, the simplest passthrough completer script would be::

    #!bin/sh
    exec $_SUBDUE_PATH_COMMAND_ --complete "$@"

But, of course, since no content examination is done in this case, the completer could also be a binary.

Note that, when the .subduecompleter file is run, the values of the environment variables ``_SUB_COMMAND_`` and ``_SUB_PATH_COMMAND_`` correspond to that of the command itself, not the completer script.

In order to allow the script to create more intelligent completions, all the parameters in the current command line being completed will be passed verbatim to the command after the ``--subdue-complete`` flag.

In order to diferentiate between the two cases below, where the caret ``^`` indicates the position of the cursor when hitting tab for completion::

  exa dothis --p
                ^

  exa dothis --p
                 ^

Subdue will pass an empty string as the last argument in the second invokation. The command author can choose to ignore this.

.. It would be great if womehow one could reuse existing completion functionaity ffrom the shell. For instance, if my subcommand is a symlink to ls, it wouldideally use ls's completion.


Notable differences with other subcommand based commands
--------------------------------------------------------

Other subcommand based commands like git or any sub created using 37signal's sub scan all the directories in the ``$PATH`` looking for executable files that start with the name of the main command. Subdue does not do that. A subcommand must be included explicitly.

Subdue supports multiple subcommand levels.

Subdue is highly configurable

Subdue holds the core separately so that it can be updated independently.

.. TODO Provide an option (argument in main) to enable this?

The parameters of ``subdue.sub.main``
-------------------------------------

.. function: main([argv=None, root_path=None, command_runner=None])

- The path to the root
- The command runner
- The prefix for eval commands ('sh-')
- The extension for completers ('subduecompleter')
- The help file extension ('helptext')
- Help processor: Code that takes the help text and reformats it (DefaultHelpProcessor)
- Line before summaries (These are the available subcommands for exa)
- Summary formatter



Inspiration and history
-----------------------

Subdue is mainly inspired in a project called "sub" by 37 Signals. I started using that but it was soon clear that it was too limited for my needs, mainly its lack of support for multi-level subcommands. Although some attempts were made to provide "sub" with "sub sub [sub...] commands", the code got too complex to follow (sub is written in Bash scripting) and modify. I still tried to add the feature, but shell scripting did not make for very clear code.

I wanted to add some more features to the very simple 'sub' project, but since it had already become much more than a script gluing a couple of commands together, I ditched shell scripting and started a rewrite in Python.

The overall structure was the same, there was a main monolithic file that had all the logic and it lived within the sub. This turned out to be a problem when I started to create more and more subs, since I found myself symlinking all their drivers to the development repository in my box. Such pattern made me realise that it would be better to make the drivers a thin layer on top of a powerful central framework that one can upgrade once and take advantage of everywhere instantaneously.

This meant a big redesign of everything from scratch, hence the start of a new project with a new name: Subdue, with the idea that it will help bring a collection of little scripts under the control of a meaningful common parent.


License
-------

Subdue is distributed under the MIT License. Please see the LICENSE file for details.
