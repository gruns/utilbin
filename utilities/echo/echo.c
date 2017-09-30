// Copyright _!_
//
// License _!_
//
// Original author: Ansgar Grunseid

#include <stdio.h>
#include <string.h>

#define BUFSIZE 65536

int mirror(char *s, char *outbuf) {
  strcpy(outbuf, s);
  return strlen(s);
}

int main(int argc, char **argv) {
  if (argc < 2 || argc > 3 || !!strcmp(argv[1], "mirror"))
    return -1;

  int nbytes;
  char buf[BUFSIZE];
  if (argc == 3)
    printf("%s", argv[2]);
  else
    while (!feof(stdin))
      if ((nbytes = fread(buf, 1, BUFSIZE, stdin)) >= 0 && !ferror(stdin))
        fprintf(stdout, buf, nbytes);

  return 0;
}
