
#ifndef FOO_H2
#define FOO_H2
#include <sstream>
#include <string>
#include <map>
#include <vector>
using namespace std;

string shiftJISToUTF8(string shiftJISStr);
void DivideDateYYMMDDHHMM(int Date, int& Year, int& Month, int& Day, int& Hour, int& Minute);
void DivideDateYYMMDDHHMM(long long Date, int& Year, int& Month, int& Day, int& Hour, int& Minute);
int Str2Int(string num);
//string IntToString(int n);
string Int2Str(int n);
string Int2Str(unsigned short  n);
string Int2Str(int n, int Keta);
string Long2Str(long  n);
char* String2Char(string Str);
string Double2Str(double n, int Keta);
void EraseString(string &Str, const string EraseWard);
void EraseString2Byte(string &Str, const string EraseWard);
int AddString(string &Str, const string AddWard, const string Condition, int StartNum, int SegmentNum);
void GetHeader(char *Buff, vector<string>&vecHeader);
void GetHeader(char *Buff, vector<string>&vecHeader, char *IgnoreWard);
void GetValueStr2StrReuse(char *Buff, const vector<string>&vecHeader, map<string, string>&mapValue);
void GetValueStr2StrReuse(char *Buff, const vector<string>&vecHeader, map<string, string>&mapValue, char *IgnoreWard);
void GetValueStr2Str(char *Buff, const vector<string>&vecHeader, map<string, string>&mapValue);
void GetValueStr2Str(char *Buff, const vector<string>&vecHeader, map<string, string>&mapValue, char *IgnoreWard);
void GetValueInt2StrReuse(char *Buff, map<int, string>&mapValue);
void GetValueInt2StrReuse(char *Buff, map<int, string>&mapValue, char *IgnoreWard);
void GetValueInt2Str(char *Buff, map<int, string>&mapValue);
void GetValueInt2Str(char *Buff, map<int, string>&mapValue, const char *IgnoreWard);
void GetValueInt2StrMavPosLog(char* Buff, map<int, string>& mapValue, const char* IgnoreWard);
void GetValueInt2Str(char* Buff, vector<string>& vecValue, const char* IgnoreWard);
void GetValueInt2Str(char* Buff, map<int, string>& mapValue, const char* IgnoreWard, const char* SegmentWard);
void GetValueInt2Str(char* Buff, map<int, string>& mapValue, const char* IgnoreWard, int endNum);
void GetValueSou(char *Buff, map<string, string>&mapValue);
void GetValueSou(char* Buff, map<string, string>& mapValue, vector<string>&vecColums);
//void GetValueStr2Str(char *, const vector<string>, map<string,string>);
//void GetValueInt2Str(char *, map<int, string>);
void GetValueInt2Str(wchar_t *Buff, map<int, wstring>&mapValue, wchar_t *IgnoreWard);

string UnixTime2Days(string UnixTimeStamp);
string Char2Str(string str);


#endif