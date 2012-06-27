(Please excuse the mess while I learn how to use source-control for the first time.)

Outlaws-Map-Converter
=====================

Work-in-progress. A script to take map files from the LucasArts Outlaws game and convert them into a format suitable for more modern FPS engines.


Outlaws is a spaghetti-western-style shooter created by LucasArts in 1996. I played it as a child, and recently reinstalled it for a bit of nostalgia.
I enjoyed the gameplay, I enjoyed the maps, I enjoyed the art and sound and whatnot, and it made me sad to think that it was all locked up in such an old and forgotten game. After discovering that most of the level data comes in plaintext, I was inspired to create a script to parse the various game files and recreate an Outlaws level in a more modern format.

It turned out to be a hopelessly ambitious idea, and I'll probably never finish it myself.

The community for this game is long gone, so I'm basically reverse-engineering everything manually with the help of all the modding utilities I could find that didn't 404. Because of this only a small portion of the project is actual code. The rest is me struggling to understand how the data is stored, what all the random numbers stand for, and how the engine translated them into geometry. Eventual goal is to output a .obj file or something similar.


(If anybody knows of an existing tool that can do this, I would be very interested in knowing about it)