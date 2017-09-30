// Copyright _!_
//
// License _!_
//
// Original author: Ansgar Grunseid

//
// Simple base64 codec wrapper around http://libb64.sourceforge.net/ that
// encodes and decodes base64 from stdin to stdout.
//

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "cencode.h"
#include "cdecode.h"

#define BUFSIZE 65536
#define USAGE "Usage: b64codec (encode | decode) [input]\n"

int printAndExit(char *str, int rc) {
  printf("%s", str);
  exit(rc);
}

// For reasons likely related to CLI usage, but inexplicably inconsistent
// between encode and decode, libb64's base64_encode_blockend() function appends
// a trailing newline '\n' character to the output buffer on encode. See
//
//   *codechar++ = '\n';
//
// of base64_encode_blockend() in libb64/src/cencode.c. Truncate this
// unnecessary newline character.
int base64_encode_blockend_no_newline(char *outbuf, base64_encodestate *state) {
  int len = base64_encode_blockend(outbuf, state);
  len -= 1;
  outbuf[len] = '\0'; // Replace the unnecessary newline with null.
  return len;
}

int encodeStr(char *s, int len, char *outbuf) {
  // <outbuf> must be at least (2*len) bytes, or twice the size of <s>.
  base64_encodestate state;
  base64_init_encodestate(&state);

  int outlen = base64_encode_block(s, len, outbuf, &state);
  outlen += base64_encode_blockend_no_newline(outbuf + outlen, &state);
  base64_init_encodestate(&state);

  return outlen;
}

void encodeFile(FILE *inf, FILE *outf) {
  int outlen;
  char inbuf[BUFSIZE];
  char outbuf[2 * BUFSIZE];
  base64_encodestate state;

  base64_init_encodestate(&state);
  while (!feof(inf)) {
    int inlen = fread(inbuf, 1, BUFSIZE, inf);
    if (inlen < 0 || ferror(inf))
      printAndExit("Error reading input. Exiting.", -1);

    outlen = base64_encode_block(inbuf, inlen, outbuf, &state);
    fprintf(outf, outbuf, outlen);
  }
  outlen = base64_encode_blockend_no_newline(outbuf, &state);
  fprintf(outf, outbuf, outlen);
  base64_init_encodestate(&state);
}

int decodeStr(char *s, int len, char *outbuf) {
  // <outbuf> must be at least (2*len) bytes, or twice the size of <s>.
  base64_decodestate state;
  base64_init_decodestate(&state);

  int outlen = base64_decode_block(s, len, outbuf, &state);
  base64_init_decodestate(&state);

  return outlen;
}

void decodeFile(FILE *inf, FILE *outf) {
  char inbuf[BUFSIZE];
  char outbuf[2 * BUFSIZE];
  base64_decodestate state;

  base64_init_decodestate(&state);
  while (!feof(inf)) {
    int inlen = fread(inbuf, 1, BUFSIZE, inf);
    if (inlen < 0 || ferror(inf))
      printAndExit("Error reading input. Exiting.", -1);

    int outlen = base64_decode_block(inbuf, inlen, outbuf, &state);
    fprintf(outf, outbuf, outlen);
  }
  base64_init_decodestate(&state);
}

int main(int argc, char **argv) {
  if (argc <= 1 || argc > 3)
    printAndExit(USAGE, -1);

  char *instr = (argc == 3) ? argv[2] : NULL;
  char *outbuf = instr ? malloc(2 * strlen(instr)) : NULL;

  if (!strcmp(argv[1], "encode")) {
    if (!instr)
      encodeFile(stdin, stdout);
    else {
      int outlen = encodeStr(instr, strlen(instr), outbuf);
      fprintf(stdout, outbuf, outlen);
    }
  } else if (!strcmp(argv[1], "decode")) {
    if (!instr)
      decodeFile(stdin, stdout);
    else {
      int outlen = decodeStr(instr, strlen(instr), outbuf);
      fprintf(stdout, outbuf, outlen);
    }
  } else
    printAndExit(USAGE, -1);

  return 0;
}
