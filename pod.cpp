#include <array>
#include <thread>
#include <stdio.h>
#include <chrono>
#include <vector>
#include <time.h>
#include <iostream>
#include <iterator>
#include <unistd.h>
#include "stdlib.h"
#include <cstring>
#include <spawn.h>

#include <string>
#include <sstream>
#include <fstream>
#include <algorithm> 

#include <sys/types.h>
#include <sys/wait.h>
#include <sys/stat.h>
#include <stdlib.h>

#include <experimental/filesystem>

using namespace std;
using namespace std::chrono_literals;

namespace fs = std::experimental::filesystem;

int main(int argc, char* argv[])
{

    vector<string> camera_data(argv, argv+argc);
    //camera_data.erase(camera_data.begin());

    string text = camera_data[1];
    string delimiter = ",";
    vector<string> capture_data{};

    size_t pos = 0;
    while ((pos = text.find(delimiter)) != string::npos) {
        capture_data.push_back(text.substr(0, pos));
        text.erase(0, pos + delimiter.length());
    }
    std::cout << "CHANNEL ID " << capture_data[0] << " CAMERA ID " << capture_data[1]  << " CAMERA POSITION  " << capture_data[2]  << " CHANNEL SIZE " << capture_data[3]  <<" MARGIN LEFT " << capture_data[4]  <<" MARGIN TOP " << capture_data[5]  <<" HEIGHT  " << capture_data[6]  <<" WIDTH " << capture_data[7]  <<" SCREEN SIZE " << capture_data[3]  << " VECTOR SIZE " << capture_data.size() <<std::endl;
    
    if(capture_data.size() > 0){
        pid_t p;
        std::string uri = capture_data[0]+","+capture_data[1]+","+capture_data[2]+","+capture_data[3]+","+capture_data[4]+","+capture_data[5]+","+capture_data[6]+","+capture_data[7]+",";
        std::cout << "URI " << uri  <<std::endl;

        fprintf(stderr, "About to spawn commandcenter process from pid %d\n", getpid());

        const char* args[] = {
            "./COMMANDCENTER",
            uri.c_str(),
            uri.c_str(),
            "COMMANDCENTERPID",
            nullptr,
            nullptr
        };

        int r = posix_spawn(&p, "./COMMANDCENTER", nullptr, nullptr,
                    (char**) args, nullptr);

        fprintf(stderr, "Child pid %d should run my commandcenter\n", p);

        char * COMMANDCENTERPID =(char*) malloc(6);
        sprintf(COMMANDCENTERPID, "%d", p);
    }
    
    return 0;
}
