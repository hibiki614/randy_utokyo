
//#ifndef FOO_H
#define FOO_H

#include <string>
//#include <map>
//#include <vector>
using namespace std;

FILE* FileOpen(string FileName, string OpenType);
FILE* FileOpen(string FileName, string OpenType, int Log);
FILE* FileOpen(string FileName, string OpenType, string messege);

//#endif