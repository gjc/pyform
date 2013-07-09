off statistics;
off finalstats;
#ifndef `PIPES_'
#message "This program must be called from within python."
#terminate
#endif
#setexternal `PIPE1_'
* The channel
#prompt READY
.sort
#toexternal "GO\n"
* symbol definition
#fromexternal
.sort
#fromexternal
.sort
#fromexternal
.sort
#toexternal "%E\n", exc
#toexternal "OVER\n"
.end


