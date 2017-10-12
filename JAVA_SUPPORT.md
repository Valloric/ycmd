OK take a deep breath, this is a monster PR.

First and foremost, massive thanks to @bstaletic and @micbou for helping not
only with the development and testing, but also for moral support!

# Overview

This PR implements native support in ycmd for the Java language, based on
[jdt.ls][]. In summary, the following key features are supported:

* Installation of jdt.ls (built from source with `build.py`)
* Management of the jdt.ls server instance, projects etc.
* A generic (ish) implementation of a [Language Server Protocol][lsp] client so
  far as is required for jdt.ls (easily extensible to other engines)
* Support for the following Java semantic engine features:
  * Semantic code completion, including automatic imports
  * As-you-type diagnostics
  * GoTo including GoToReferences
  * FixIt
  * RefactorRename
  * GetType
  * GetDoc

See the [trello board][trello] for a more complete picture.

# Why is this necessary and useful?

The current state of the plugin for YCM support for Java is basically [eclim][]
or [javacomplete2][], neither of which work perfectly with ycmd, and neither of
which are quite as well integrated as we might like.

## eclim

Eclim is actually pretty good and I have used it for a long time. However, the
experience isn't optimal for YCM:

### Pros

* Pretty good project creation, management functions
* Lots of languages (supports more than just Java)
* Lots of features (supports nearly all the standard YCMD commands)
* New class creation, and lots of other stuff like that

### Cons

* It's a pain to set up (I know of only 1 other person at my company who has
  successfully got it working), requiring a Vimball, installation into an
  existing eclipse installation, manually starting the server, and other fiddly
  stuff.
* Diagnostics are delivered via Syntastic, so block the UI on save, and at a
  number of other times.
* Requires eclipse installation and understanding

## javacomplete2

I have not extensively used javacomplete2, but I know there have been issues
reported that its omnifunc doesn't always play nice with ycmd.

### Pros?

* Very simple to get going
* Seems to give completion suggestions reasonably well

### Cons?

* Lacks features
* No diagnostics ?
* Lots of vimscript (java parser in vimscript?)

## Notable mentions

* [vim-lsp][] seems to be a plugin for generic [LSP][lsp] support. I haven't
  tried it but my experience with jdt.ls is that there is no way to make a fully
  working LSP client without server-specific knowledge. I don't know if this
  works with jdt.ls

# Why jdt.ls?

I tried 2 different Java LSP engines:

* [vscode-javac][]: javac (the Java compiler) is the backend. Actually,
  this is a nice and simple server and has decent features.
* [jdt.ls][]: Eclipse JDT as a server daemon. This appears to be the most
  popular Java plugin for [VSCode][], and has the full power of RedHat and
  Microsoft investing in bringing JDT (the eclipse Java engine) to VSCode and
  the LSP-using community.

Initially, for its simplicity, I was [drawn to vscode-javac](https://github.com/puremourning/ycmd-1/commit/9180e963897edbe2c5e6695d8f04eff15d681c8a)
for its simplicity and ease of integration with ycmd. However, I also
implemented [jdt.ls][] and found this, while more work, to be a superior
experience. It also has a very active development community, which bodes well
for the future.

# Why such a big PR, man. Come on!

I'm sorry. I really really am. I honestly tried to rebase and rewrite the ~150
commits over the last 1 year or so, but as with many such things, a lot of the
functionality that would make "Phase 1" ended up relying on functionality and
test framework that came in "Phase N". So I'm dumping this on you in one
unwieldy heap and hoping that you can find it in your hearts to forgive me. I
honestly spent hours trying :(

# OK, but come on, give us a hand...

Sure thing! I've tried to give below a "review guide" to help you get your heads
around what's going on an why some of the design decisions where made.

## Overall design/goals

Key goals:

1. Support Java in ycmd and YCM; make it good enough to replace eclim and
   javacomplete2 for most people
2. Make it possible/easy to support other [lsp][] servers in future (but, don't
   suffer from yagni); prove that this works.

An overview of the objects involved can be seen on [this
card][design]. In short:

* 2 classes implement the language server protocol in the
  `language_server_completer.py` module:
 * `LanguageServerConnection` - an abstraction of the comminication with the
   server, which may be over stdio or any number of TCP/IP ports (or a domain
   socket, etc.). Only a single implementation is included (stdio), but
   [implementations for TCP/IP](https://github.com/puremourning/ycmd-1/commit/f3cd06245692b05031a64745054326273d52d12f)
   were written originally and dropped in favour of stdio's simplicity.
 * `LanguageServerCompleter` - an abstract base for any completer based on LSP,
   which implements as much standard functionality as possible including
   completions, diagnostics, goto, fixit, rename, etc.
* The `java_completer` itself implements the `LanguageServerCompleter`, boots
  the jdt.ls server, and instantiates a `LanguageServerConnection` for
  communication with jdt.ls.

The overall plan and some general discussion around the project can be found on
the [trello board][trello] I used for development.

## Threads, why oh why so many threads.

OK chill. It's not thhaartd.

LSP is by its nature an asyncronous protocol. There are request-reply like
`requests` and unsolicited `notifications`. Receipt of the latter is mandatory,
so we cannot rely on their being a `bottle` thread executing a client request.

So we need a message pump and despatch thread. This is actually the
`LanguageServerConnection`, which implements `thread`. It's main method simply
listens on the socket/stream and despatches complete messages to the
`LanguageServerCompleter`. It does this:

* For `requests`: similarly to the TypeScript completer, using python `event`
  objects, wrapped in our `Response` class
* For `notifications`: via a synchronised `queue`. More on this later.

A very poor representation of this is on the "Requests and notifications" page
of the [design][], including a rough sketch of the thread interaction.

### Some handling is done in the message pump.

That's right. There are certain notifications which we have to handle when we
get them, such as:

* Initialisation messages
* Diagnostics

In these cases, we allow some code to be executed inline within the message pump
thread, as there is no other thread guaranteed to execute. These are handled by
callback functions and mutexes.

## Startup sequence

See the 'initialisation sequence' tab on the [design][] for a bit of background.

In standard LSP, the initialisation sequence consists of an initialise
request-reply, followed by us sending the server an initialised notification. We
must not send any other requests until this has completed.

An additional wrinkle is that jdt.ls, being based on eclipse has a whole other
initialisation sequence during which time it is not fully functional, so we have
to determine when that has completed too. This is done by jdt.ls-specific
messages and controls the `ServerIsReady` response.

In order for none of these shenanigans to block the user, we must do them all
asynchronously, effectively in the message pump thread. In addition, we must
queue up any file contents changes during this period to ensure the server is up
to date when we start processing requests proper.

This is unfortunately complicated, but there were early issues with really bad
UI blocking that we just had to get rid of.

## Completion foibles

Language server protocol requires that the client can apply textEdits,
rather than just simple text. This is not an optional feature, but ycmd
clients do not have this ability.

The protocol, however, restricts that the edit must include the original
requested completion position, so we can perform some simple text
manipulation to apply the edit to the current line and determine the
completion start column based on that.

In particular, the jdt.ls server returns textEdits that replace the
entered text for import completions, which is one of the most useful
completions.

We do this super inefficiently by attempting to normalise the TextEdits
into insertion_texts with the same start_codepoint. This is necessary
particularly due to the way that eclipse returns import completions for
packages.

We also include support for "additionalTextEdits" which
allow automatic insertion of, e.g.,  import statements when selecting
completion items. These are sent on the completion response as an
additional completer data item called 'fixits'. The client applies the
same logic as a standard FixIt once the selected completion item is
inserted.

## Diagnostics foibles

Diagnostics in LSP are delivered asynchronously via `notifications`. Normally,
we would use the `OnFileReadyToParse` response to supply diagnostics, but due to
the lag between refreshing files and receiving diagnostics, this leads to a
horrible user experience where the diagnostics always lag one edit behind.

To resolve this, we use the long-polling mechanism added here (`ReceiveMessages`
request) to return diagnostics to the client asynchronously.

We deliver asynchronous diagnostics to the client in the same way that the
language server does, i.e. per-file. The client then fans them out or does
whatever makes sense for the client. This is necessary because it isn't possible
to know when we have received all diagnostics, and combining them into a single
message was becoming clunky and error prone.

In order to be relatively compatible with other clients, we also return
diagnostics on the file-ready-to-parse event, even though they might be
out of date wrt the code. The client is responsible for ignoring these
diagnostics when it handles the asynchronously delivered ones. This requires
that we hold the "latest" diagnostics for a file. As it turns out, this is also
required for FixIts.

## Projects

jdt.ls is based on eclipse. It is in fact an eclipse plugin. So it requires an
eclipse workspace. We try and hide this by creating an ad-hoc workspace for each
ycmd instance. This prevents the possibility of multiple "eclipse"  instances
using the same workspace, but can lead to unreasonable startup times for large
projects.

The jdt.ls team strongly suggest that we should re-use a workspace based on the
hash of the "project directory" (essentially the dir containing the project
file: `.project`, `pom.xml` or `build.gradle`). They also say, however, that
eclipse frequently corrupts its workspace.

So we have a hidden switch to re-use a workspace as the jdt.ls devs suggest. In
testing at work, this was _mandatory_ due to a slow SAN, but at home, startup
time is not an issue, even for large projects. I think we'll just have to see
how things go to decide which one we want to keep.

## Subcommand foibles

### GetDoc/GetType

There is no GetType in LSP. There's only "hover". The hover response is
hilariously server-specific, so in the base `LanguageServerCompleter` we just
provide the ability to get the `hover` response and `JavaCompleter` extracts the
appropriate info from there. Thanks to @bstaletic for this!

### FixIt

FixIts are implemented as code actions, and require the diagnostic they relate
to to be send from us to the server, rather than just a position. We use the
stored diags and find the nearest one based on the `request_data`.

What's worse is that the LSP provides _no documentation_ for what the "Code
action" response should be, and it is 100% implementation-specific. They just
have this `command` abstraction which is basically "do a thing".

From what I've seen, most servers just end up with either a `WorkspaceEdit` or a
series of `TextEdits`, which is fine for us as that's what ycmd's protocol looks
like.

The solution is that we have a callback into the `JavaCompleter`  to handle the
(custom) `java.apply.workspaceEdit` "command".

### GoToReferences

Annoyingly, jdt.ls sometimes returns references to .class files within jar
archives using a custom `jdt://` protocol. We can't handle that, so we have to
dodge and weave so that we don't crash.

### Stopping the server

Much like the initialisation sequence, the LSP shutdown sequence is a bit
fiddly. 2 things are required:

1. A `shutdown` request-reply. The server tides up and _prepares to die!_
2. An `exit` notification. We tell the server to die.

This isn't so bad, but jdt.ls is buggy and actually dies without responding to
the `shutdown` request. So we have a bunch of code to handle that and to ensure
that the server dies eventually, as it had a habbit of getting stuck running,
particularly if we threw an exception.

# Closing remarks

Phew. That was a lot of caveats! I have personally used this quite a lot now,
and it has proven to be really useful. In particular the full index and
GoToReferences, etc.

I think the tests are comprehensive, but there is probably more work to do on
coverage. Some of it will be tricky (particularly exceptions around `jdt:` and
other edge cases in jdt.ls that I've come across).

## Ship it as experimental ?

Due to the rapid pace of development of jdt.ls and the scale of this change, one
thought I had was to mark Java support in YCM as _exprrimental_ and gather
feedback via an open github issue. I'm certain there will be issues, and
preferences, etc. so this might be a good way to tackle that.

# Where's the client PR ?

I haven't finished polishing the client yet, but you can get use it by checking
out [my `language-server-java` branch of YCM][client].

[jdt.ls]: https://github.com/eclipse/eclipse.jdt.ls
[lsp]: https://github.com/Microsoft/language-server-protocol/
[eclim]: http://eclim.org
[javacomplete2]: https://github.com/artur-shaik/vim-javacomplete2
[vscode-javac]: https://github.com/georgewfraser/vscode-javac
[VSCode]: https://code.visualstudio.com
[destign]: https://trello.com/c/78IkFBzp
[trello]: https://trello.com/b/Y6z8xag8/ycm-java-language-server
[client]: https://github.com/puremourning/YouCompleteMe/tree/language-server-java
