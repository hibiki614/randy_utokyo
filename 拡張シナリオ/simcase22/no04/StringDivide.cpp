//#include <sstream>
#define _CRT_SECURE_NO_WARNINGS 1
#include <string>
#include <map>
#include <vector>
#include <time.h>
#include "StringDivide.h"
using namespace std;

//string IntToString(int number)
//{
//	stringstream ss;
//	ss << number;
//	return ss.str();
//}

#include <iostream>
#include <sstream>
#include <fstream>
#include <codecvt>
string shiftJISToUTF8(string shiftJISStr) {
	// Shift-JISからワイド文字列へ変換
	std::wstring_convert<std::codecvt<wchar_t, char, std::mbstate_t>, wchar_t> converter(new std::codecvt<wchar_t, char, std::mbstate_t>("Japanese_Japan.932"));
	std::wstring wideStr = converter.from_bytes(shiftJISStr);

	// ワイド文字列からUTF-8文字列へ変換
	std::wstring_convert<std::codecvt_utf8<wchar_t>> utf8Converter;
	return utf8Converter.to_bytes(wideStr);
}
void DivideDateYYMMDDHHMM(int Date, int& Year, int& Month, int& Day, int& Hour, int& Minute) {
	Year = Date / 100000000;
	Date %= 100000000;
	Month = Date / 1000000;
	Date %= 1000000;
	Day = Date / 10000;
	Date %= 10000;
	Hour = Date / 100;
	Date %= 100;
	Minute = Date;
}

void DivideDateYYMMDDHHMM(long long Date, int& Year, int& Month, int& Day, int& Hour, int& Minute) {
	Year = Date / 100000000;
	Date %= 100000000;
	Month = Date / 1000000;
	Date %= 1000000;
	Day = Date / 10000;
	Date %= 10000;
	Hour = Date / 100;
	Date %= 100;
	Minute = Date;
}

string Int2Str(int n){
	char Buff[64];
	sprintf_s(Buff, sizeof(Buff),"%d", n);
	return Buff;
}

string Long2Str(long n) {
	char Buff[64];
	sprintf_s(Buff, sizeof(Buff), "%ld", n);
	return Buff;
}

string Int2Str(unsigned short n) {
	char Buff[64];
	sprintf_s(Buff, sizeof(Buff), "%u", n);
	return Buff;
}

string Int2Str(int n, int Keta){
	char Buff[64] ="";
	string Str;
	if (Keta == 0)sprintf_s(Buff, sizeof(Buff), "%d", n);
	if (Keta == 1)sprintf_s(Buff, sizeof(Buff), "%01d", n);
	if (Keta == 2)sprintf_s(Buff, sizeof(Buff), "%02d", n);
	if (Keta == 3)sprintf_s(Buff, sizeof(Buff), "%03d", n);
	if (Keta == 4)sprintf_s(Buff, sizeof(Buff), "%04d", n);
	if (Keta == 5)sprintf_s(Buff, sizeof(Buff), "%05d", n);
	if (Keta == 6)sprintf_s(Buff, sizeof(Buff), "%06d", n);
	if (Keta == 7)sprintf_s(Buff, sizeof(Buff), "%07d", n);
	if (Keta == 8)sprintf_s(Buff, sizeof(Buff), "%08d", n);
	if (Keta == 9)sprintf_s(Buff, sizeof(Buff), "%09d", n);
	return Buff;
}
int Str2Int(string num) {
	return atoi(num.c_str());
}

string Int2Str(unsigned short n, int Keta) {
	char Buff[64] = "";
	string Str;
	if (Keta == 0)sprintf_s(Buff, sizeof(Buff), "%u", n);
	if (Keta == 1)sprintf_s(Buff, sizeof(Buff), "%01u", n);
	if (Keta == 2)sprintf_s(Buff, sizeof(Buff), "%02u", n);
	if (Keta == 3)sprintf_s(Buff, sizeof(Buff), "%03u", n);
	if (Keta == 4)sprintf_s(Buff, sizeof(Buff), "%04u", n);
	if (Keta == 5)sprintf_s(Buff, sizeof(Buff), "%05u", n);
	if (Keta == 6)sprintf_s(Buff, sizeof(Buff), "%06u", n);
	if (Keta == 7)sprintf_s(Buff, sizeof(Buff), "%07u", n);
	if (Keta == 8)sprintf_s(Buff, sizeof(Buff), "%08u", n);
	if (Keta == 9)sprintf_s(Buff, sizeof(Buff), "%09u", n);
	return Buff;
}
string Double2Str(double n, int Keta){
	//int IntMax = 2147483647;
	//           201807010006.56000
	int IntMax = 1000000000;
	char Buff[64];
	string Str;
	double nSub = n;
	int nSubRate = (int)(nSub / IntMax);
	int Rest = n - (double)(nSubRate) * IntMax;
	double RoundDownNum = (double)(nSubRate)* IntMax + Rest;

	//if (Keta == 0)sprintf_s(Buff, sizeof(Buff), "%.0lf", RoundDownNum);
	if (Keta == 0)sprintf_s(Buff, sizeof(Buff), "%.0lf", n);
	if (Keta == 1)sprintf_s(Buff, sizeof(Buff), "%.1lf", n);
	if (Keta == 2)sprintf_s(Buff, sizeof(Buff), "%.2lf", n);
	if (Keta == 3)sprintf_s(Buff, sizeof(Buff), "%.3lf", n);
	if (Keta == 4)sprintf_s(Buff, sizeof(Buff), "%.4lf", n);
	if (Keta == 5)sprintf_s(Buff, sizeof(Buff), "%.5lf", n);
	if (Keta == 6)sprintf_s(Buff, sizeof(Buff), "%.6lf", n);
	if (Keta == 7)sprintf_s(Buff, sizeof(Buff), "%.7lf", n);
	if (Keta == 8)sprintf_s(Buff, sizeof(Buff), "%.8lf", n);
	if (Keta == 9)sprintf_s(Buff, sizeof(Buff), "%.9lf", n);
	if (Keta == 10)sprintf_s(Buff, sizeof(Buff), "%.10lf", n);
	if (Keta == 11)sprintf_s(Buff, sizeof(Buff), "%.11lf", n);
	if (Keta == 12)sprintf_s(Buff, sizeof(Buff), "%.12lf", n);
	if (Keta == 13)sprintf_s(Buff, sizeof(Buff), "%.13lf", n);
	if (Keta == 14)sprintf_s(Buff, sizeof(Buff), "%.14lf", n);
	if (Keta == 15)sprintf_s(Buff, sizeof(Buff), "%.15lf", n);
	if (Keta == 16)sprintf_s(Buff, sizeof(Buff), "%.16lf", n);
	//Str = Buff;
	return Buff;
}
char* String2Char(string Str){
	char Buff[64];
	sprintf_s(Buff, sizeof(Buff), "%s", Str.c_str());
	return Buff;
}
void EraseString(string &Str, const string EraseWard){
	for (size_t c = Str.find_first_of(EraseWard.c_str()); c != string::npos; c = c = Str.find_first_of(EraseWard.c_str())){
		Str.erase(c, 1);
	}
}

void EraseString2Byte(string &Str, const string EraseWard){
	int	bcontinue = 1;
	for (size_t c = Str.find_first_of(EraseWard[0]); c != string::npos && bcontinue == 1; c = c = Str.find_first_of(EraseWard[0])){
		for (size_t d = Str.find_first_of(EraseWard[1]); d != string::npos ; d = d = Str.find_first_of(EraseWard[1])){
			if (c == d - 1){
				Str.erase(c, 2);
				bcontinue = 1;
				break;
			}
		}
		bcontinue = 0;
	}
}

//基文字列, 追加する文字, 条件, 対象開始文字番号, 調査対象文字数
int AddString(string &Str, const string AddWard, const string Condition, int StartNum, int SegmentNum){
	int check = 0;

	char str1[10];// , str2[10], cd1[10], cd2[10];
	//sprintf_s(cd1, sizeof(cd1), "%c", Condition[0]);
	//sprintf_s(cd2, sizeof(cd2), "%c", Condition[1]);
	//sprintf_s(cd3, sizeof(cd3), "%s", Condition[2]);
	//for (int n = 0; n < (int)Str.size(); n++){ //17
	//for (int n = 17; n < 22; n++){ //17
	//	sprintf_s(str1, sizeof(str1), "%c", Str[n]);
	//	if (!strcmp(str1, cd1)){
	//		if (n + 1 <(int)Str.size())
	//		sprintf_s(str2, sizeof(str2), "%c", Str[n+1]);
	//		if (!strcmp(str2, cd2)){
	//			Str.insert(n + 1, AddWard);
	//			check = 1;
	//		}
	//	}
	//}
	int AddCount = 0;
	int EndNum = StartNum + SegmentNum - 1;
	if ((int)Str.size() < EndNum) EndNum = (int)Str.size();
	for (int n = StartNum; n < EndNum + AddCount; n++){
		//string str2 = "" + Str[n] + Str[n + 1];
		sprintf_s(str1, sizeof(str1), "%c%c", Str[n], Str[n+1]);
		if (!strcmp(str1, Condition.c_str())){
			Str.insert(n + 1, AddWard);
			AddCount += (int)AddWard.size(); //追加された文字列の総数
			n += (int)AddWard.size(); //次の読み込み文字を追加した文字列のサイズだけずらす。
			check = 1;
		}
	}
	//for (int n = Start; n < End; n++){ //17
	//	sprintf_s(str1, sizeof(str1), "%c%c", Str[n], Str[n + 1]);
	//	if (!strcmp(str1, Condition.c_str())){
	//		Str.insert(n + 1, AddWard);
	//		check = 1;
	//	}
	//}
	return check;
}

void GetHeader(char *Buff, vector<string>&vecHeader){
	char *tp, *next;
	const char *IgnoreWard = ",\n";
	tp = strtok_s(Buff, IgnoreWard, &next);
	vecHeader.push_back(tp);
	while (strlen(next) > 1){
		tp = strtok_s(NULL, IgnoreWard, &next);
		vecHeader.push_back(tp);
	}
}

void GetHeader(char *Buff, vector<string>&vecHeader, char *IgnoreWard){
	char *tp, *next;
	tp = strtok_s(Buff, IgnoreWard, &next);
	vecHeader.push_back(tp);
	while (strlen(next) > 1){
		tp = strtok_s(NULL, IgnoreWard, &next);
		vecHeader.push_back(tp);
	}
}

//mapをクリアしないver
//列数が安定している場合に使用
void GetValueStr2StrReuse(char *Buff, const vector<string>&vecHeader, map<string, string>&mapValue, char *IgnoreWard){
	char *tp, *next;
	int n = 0;
	if (Buff != NULL && n < (int)vecHeader.size()){
		tp = strtok_s(Buff, IgnoreWard, &next);
		mapValue[vecHeader[n].c_str()] = tp;
		n++;
		while (strlen(next) > 1){
			tp = strtok_s(NULL, IgnoreWard, &next);
			if (n < (int)vecHeader.size()){
				mapValue[vecHeader[n].c_str()] = tp;
				n++;
			}
			else{
				return;
			}
		}
	}
	return;
}
void GetValueStr2StrReuse(char *Buff, const vector<string>&vecHeader, map<string, string>&mapValue){
	char *tp, *next;
	const char *IgnoreWard = "\n,";
	int n = 0;
	if (Buff != NULL && n < (int)vecHeader.size()){
		tp = strtok_s(Buff, IgnoreWard, &next);
		mapValue[vecHeader[n].c_str()] = tp;
		n++;
		while (strlen(next) > 1){
			tp = strtok_s(NULL, IgnoreWard, &next);
			if (n < (int)vecHeader.size()){
				mapValue[vecHeader[n].c_str()] = tp;
				n++;
			}
			else{
				return;
			}
		}
	}
	return;
}
void GetValueStr2Str(char *Buff, const vector<string>&vecHeader, map<string, string>&mapValue, char *IgnoreWard){
	char *tp, *next;
	int n = 0;
	mapValue.clear();
	if (Buff != NULL && n < (int)vecHeader.size()){
		tp = strtok_s(Buff, IgnoreWard, &next);
		mapValue[vecHeader[n].c_str()] = tp;
		n++;
		while (strlen(next) > 1){
			tp = strtok_s(NULL, IgnoreWard, &next);
			if (n < (int)vecHeader.size()){
				mapValue[vecHeader[n].c_str()] = tp;
				n++;
			}
			else{
				return;
			}
		}
	}
	return;
}

void GetValueStr2Str(char *Buff, const vector<string>&vecHeader, map<string, string>&mapValue){
	const char *IgnoreWard = ",\n";
	char *tp, *next;
	int n = 0;
	mapValue.clear();
	if (Buff != NULL && n < (int)vecHeader.size()){
		tp = strtok_s(Buff, IgnoreWard, &next);
		mapValue[vecHeader[n].c_str()] = tp;
		n++;
		while (strlen(next) > 1){
			tp = strtok_s(NULL, IgnoreWard, &next);
			if (n < (int)vecHeader.size()){
				mapValue[vecHeader[n].c_str()] = tp;
				n++;
			}
			else{
				return;
			}
		}
	}
	return;
}

//mapをクリアしないver
//列数が安定している場合に使用
void GetValueInt2StrReuse(char *Buff, map<int, string>&mapValue){
	char *tp, *next;
	const char *IgnoreWard = "\n,";
	int n = 0;
	if (Buff != NULL){
		tp = strtok_s(Buff, IgnoreWard, &next);
		mapValue[n] = tp;
		n++;
		while (strlen(next) > 1){
			tp = strtok_s(NULL, IgnoreWard, &next);
			if (tp != NULL){
				mapValue[n] = tp;
				n++;
			}
		}
	}
	return;
}

void GetValueInt2StrReuse(char *Buff, map<int, string>&mapValue, char *IgnoreWard){
	char *tp, *next;
	int n = 0;
	if (Buff != NULL){
		tp = strtok_s(Buff, IgnoreWard, &next);
		mapValue[n] = tp;
		n++;
		while (strlen(next) > 1){
			tp = strtok_s(NULL, IgnoreWard, &next);
			if (tp != NULL){
				mapValue[n] = tp;
				n++;
			}
		}
	}
	return;
}

void GetValueInt2Str(char *Buff, map<int, string>&mapValue){
	char *tp, *next;
	const char *IgnoreWard = ",\n";
	int n = 0;
	mapValue.clear();
	if (Buff != NULL){
		tp = strtok_s(Buff, IgnoreWard, &next);
		mapValue[n] = tp;
		n++;
		while (strlen(next) > 1){
			tp = strtok_s(NULL, IgnoreWard, &next);
			if (tp != NULL){
				mapValue[n] = tp;
				n++;
			}
		}
	}
	return;
}


void GetValueInt2Str(char *Buff, map<int, string>&mapValue, const char *IgnoreWard){
	char *tp, *next;
	int n = 0;
	mapValue.clear();
	if (Buff != NULL){
		tp = strtok_s(Buff, IgnoreWard, &next);
		if (tp != NULL) {
			mapValue[n] = tp;
			n++;
			while (strlen(next) > 0){
				if (!strcmp(next, "\n")) return;
				tp = strtok_s(NULL, IgnoreWard, &next);
				if (tp != NULL){
					mapValue[n] = tp;
					n++;
				}
			}
		}
	}
	return;
}

void GetValueInt2StrMavPosLog(char* Buff, map<int, string>& mapValue, const char* IgnoreWard) {
	char* tp, * next;
	int n = 0;
	char sub[182][64];
	mapValue.clear();
	int i = 0;
	sscanf_s(Buff,"%[^,],%[^,],%[^,],%[^,],%[^,],%[^,],%[^,],%[^,],%[^,],%[^,],%[^,],%[^,],%[^,],%[^,],%[^,],%[^,],%[^,],%[^,],%[^,],%[^,]",
		sub[0], sizeof(sub[0]),
		sub[1], sizeof(sub[1]),
		sub[2], sizeof(sub[2]),
		sub[3], sizeof(sub[3]),
		sub[4], sizeof(sub[4]),
		sub[5], sizeof(sub[5]),
		sub[6], sizeof(sub[0]),
		sub[7], sizeof(sub[1]),
		sub[8], sizeof(sub[2]),
		sub[9], sizeof(sub[3]),
		sub[10], sizeof(sub[4]),
		sub[11], sizeof(sub[5]),
		sub[12], sizeof(sub[0]),
		sub[13], sizeof(sub[1]),
		sub[14], sizeof(sub[2]),
		sub[15], sizeof(sub[3]),
		sub[16], sizeof(sub[4]),
		sub[17], sizeof(sub[5]),
		sub[18], sizeof(sub[4]),
		sub[19], sizeof(sub[5]));
	for (int n = 0; n < 20; n++) {
		mapValue[n] = sub[n];
	}
	return;
}
void GetValueInt2Str(char* Buff, vector<string>& vecValue, const char* IgnoreWard) {
	char* tp, * next;
	int n = 0;
	vecValue.clear();
	if (Buff != NULL) {
		tp = strtok_s(Buff, IgnoreWard, &next);
		if (tp != NULL) {
			vecValue.push_back(tp);
			n++;
			while (strlen(next) > 0) {
				if (!strcmp(next, "\n")) return;
				tp = strtok_s(NULL, IgnoreWard, &next);
				if (tp != NULL) {
					vecValue.push_back(tp);
					n++;
				}
			}
		}
	}
	return;
}

void GetValueInt2Str(char* Buff, map<int, string>& mapValue, const char* IgnoreWard, const char *SegmentWard) {
	char* tp, * next;
	char* tp1;
	int b_num = 0;
	map<int, string>mapBuffer;
	mapValue.clear();
	if (Buff != NULL) {
		tp1 = strtok_s(Buff, SegmentWard, &next);
		if (tp1 != NULL) {
			mapBuffer[b_num++] = tp1;
			while (strlen(next) > 0) {
				if (!strcmp(next, "\n")) return;

				tp1 = strtok_s(NULL, SegmentWard, &next);
				if (tp1 != NULL) {
					mapBuffer[b_num++] = tp1;
				}
			}
		}
	}

	int n = 0;
	int isDiv = 0;//偶数か
	while (isDiv < (int)mapBuffer.size()) {
		if (isDiv % 2 == 1) {
			mapValue[n] = mapBuffer[isDiv];
			n++;
		}
		else {
			char tmpBuff[1024];
			sprintf(tmpBuff, "%s", mapBuffer[isDiv].c_str());
			tp = strtok_s(tmpBuff, IgnoreWard, &next);
			if (tp != NULL) {
				mapValue[n] = tp;
				n++;
				while (strlen(next) > 0) {
					if (!strcmp(next, "\n")) return;

					tp = strtok_s(NULL, IgnoreWard, &next);
					if (tp != NULL) {
						mapValue[n] = tp;
						n++;
					}
				}
			}
		}
		isDiv++;
	}
	return;
}


void GetValueInt2Str(char* Buff, map<int, string>& mapValue, const char* IgnoreWard, int endNum) {
	char* tp, * next;
	int n = 0;
	mapValue.clear();
	if (Buff != NULL) {
		tp = strtok_s(Buff, IgnoreWard, &next);
		if (tp != NULL) {
			mapValue[n] = tp;
			n++;
			while (strlen(next) > 0) {
				if (!strcmp(next, "\n")) return;
				tp = strtok_s(NULL, IgnoreWard, &next);
				if (tp != NULL) {
					mapValue[n] = tp;
					n++;
					if (n > endNum) {
						return;
					}
				}
			}
		}
	}
	return;
}

void GetValueInt2Str(wchar_t *Buff, map<int, wstring>&mapValue, wchar_t *IgnoreWard){
	wchar_t *tp, *next;
	int n = 0;
	mapValue.clear();
	if (Buff != NULL){
		tp = wcstok_s(Buff, IgnoreWard, &next);
		if (tp != NULL) {
			mapValue[n] = tp;
			n++;
			while (wcslen(next) > 1){
				tp = wcstok_s(NULL, IgnoreWard, &next);
				if (tp != NULL){
					mapValue[n] = tp;
					n++;
				}
			}
		}
	}
	return;
}

void GetValueSou(char *Buff, map<string, string>&mapValue){
	char *tp1, *tp2, *next;
	const char *IgnoreWard = "=,\n	";
	int n = 0;
	mapValue.clear();
	if (Buff == NULL) return;
	tp1 = strtok_s(Buff, IgnoreWard, &next);
	tp2 = strtok_s(NULL, IgnoreWard, &next);
	if (tp1 != NULL && tp2 != NULL) mapValue[tp1] = tp2;
	if (Buff != NULL){
		while (strlen(next) > 1){
			tp1 = strtok_s(NULL, IgnoreWard, &next);
			tp2 = strtok_s(NULL, IgnoreWard, &next);
			if (tp1 != NULL && tp2 != NULL) mapValue[tp1] = tp2;
		}
	}
	return;
}



void GetValueSou(char* Buff, map<string, string>& mapValue, vector<string>& vecColums) {
	char* tp1, * tp2, * next;
	const char* IgnoreWard = "=,\n	";
	int n = 0;
	mapValue.clear();
	vecColums.clear();
	if (Buff == NULL) return;
	tp1 = strtok_s(Buff, IgnoreWard, &next);
	tp2 = strtok_s(NULL, IgnoreWard, &next);
	if (tp1 != NULL && tp2 != NULL) {
		mapValue[tp1] = tp2;
		vecColums.push_back(tp1);
	}
	if (Buff != NULL) {
		while (strlen(next) > 1) {
			tp1 = strtok_s(NULL, IgnoreWard, &next);
			tp2 = strtok_s(NULL, IgnoreWard, &next);
			if (tp1 != NULL && tp2 != NULL) {
				mapValue[tp1] = tp2;
				vecColums.push_back(tp1);
			}
		}
	}
	return;
}

string UnixTime2Days(string UnixTimeStamp){

	//if ((int)UnixTimeStamp.size() > 10){
	//	UnixTimeStamp.erase(UnixTimeStamp.begin() + 10, UnixTimeStamp.begin() + (int)UnixTimeStamp.size());
	//}
	//char       buf[80];
	//long long n = stoll(UnixTimeStamp);
	////time_t     now = (time_t)n;
	//struct tm  *ts;
	//ts = localtime(&(time_t)n);
	//
	//strftime(buf, sizeof(buf), "%Y/%m/%d %H:%M:%S", ts);
	//return buf;
	return "";
}

string Char2Str(string str){
	return str;
}
