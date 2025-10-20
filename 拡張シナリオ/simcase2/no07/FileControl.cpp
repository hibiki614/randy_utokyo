#include <string>
#include "FileControl.h"
using namespace std;

FILE* FileOpen(string FileName, string OpenType){
	FILE *fp;
	
	int err = fopen_s(&fp, FileName.c_str(), OpenType.c_str());
	if (err != 0){
		string type;
		if (OpenType == "r")type = "Read";
		if (OpenType == "w")type = "Write";
		printf("%s File Open Error : [%s]\n", type.c_str(), FileName.c_str());
		return NULL;
	}
	printf("Open File:%s\n", FileName.c_str());
	return fp;
}

FILE* FileOpen(string FileName, string OpenType, int Log){
	FILE *fp;

	int err = fopen_s(&fp, FileName.c_str(), OpenType.c_str());
	if (err != 0){
		if (Log > -1) {
			if (OpenType == "r") printf("Read File Open Error : %s\n", FileName.c_str());
			if (OpenType == "w") printf("Write File Open Error : %s\n", FileName.c_str());
		}
		return NULL;
	}
	if (Log > 0) printf("Open File:%s\n", FileName.c_str());
	return fp;
}

FILE* FileOpen(string FileName, string OpenType, string messege) {
	FILE* fp;

	int err = fopen_s(&fp, FileName.c_str(), OpenType.c_str());
	if (err != 0) {
		string type;
		if (OpenType == "r")type = "Read";
		if (OpenType == "w")type = "Write";
		printf("%s File Open Error : [%s] %s\n", type.c_str(), FileName.c_str(), messege.c_str());
		return NULL;
	}
	printf("Open File:%s\n", FileName.c_str());
	return fp;
}