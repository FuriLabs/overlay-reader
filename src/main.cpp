#include <overlay-reader.h>

#include <string.h>
#include <iostream>
#include <sstream>

using namespace std;

int findArgvIndex(const char *argv, char *argvs[], int count);
const char* getArgv(const char* argv, char *argvs[], int count);
void printHelp(const char *self_name);

int main(int argc, char *argv[]) {
	const char* path = getArgv("-p", argv, argc);
	const char* target = getArgv("-t", argv, argc);
	const char* config = getArgv("-c", argv, argc);
	const char* subtype = getArgv("-s", argv, argc);
	std::string ret;

	if (!path && !target)
	{
		printHelp(argv[0]);
		return -1;
	}
	else if (getArgv("-h", argv, argc) != nullptr)
	{
		printHelp(argv[0]);
	}
	if (!config) {
		printHelp(argv[0]);
		return -1;
	}
    if (!subtype)
        subtype = "";

	if (target)
		ret = overlayreader::GetConfigByTarget(target, config, subtype, "Failed to get value");
	else if (path)
		ret = overlayreader::GetConfigByPath(path, config, subtype, "Failed to get value");

	printf("%s\n", ret.c_str());
	return 0;
}

int findArgvIndex(const char* argv, char *argvs[], int count) {
	for(int i = 0 ; i<count ; i++) {
		if(strcmp(argv, argvs[i])==0) {
			return i;
		}
	}
	return -1;
}

const char* getArgv(const char* argv, char *argvs[], int count) {
	int index = findArgvIndex(argv, argvs, count);
	if(index>=0 && index+1 < count) {
		return argvs[index+1];
	}
	return nullptr;
}

void printHelp(const char* self_name) {
	cout <<self_name<<" <-p path or -t target> <-c config> [-s subtype]" <<endl<<endl;
	cout <<"-p : Set path of overlay.apk" <<endl;
	cout <<"-t : Select overlay package target (value of android:targetPackage in rro manifest)" <<endl;
	cout <<"-c : Select the config to show" << endl;
	cout <<"-s : Input sub type of config (like mcc310-mnc580)" << endl;
}
