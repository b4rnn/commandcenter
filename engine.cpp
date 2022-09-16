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

    std::cout << "URI " << camera_data[0]  <<std::endl;

    string text = camera_data[1];
    string delimiter = ",";
    vector<string> capture_data{};

    size_t pos = 0;
    while ((pos = text.find(delimiter)) != string::npos) {
        capture_data.push_back(text.substr(0, pos));
        text.erase(0, pos + delimiter.length());
    }

    std::cout << "CHANNEL ID " << capture_data[0] <<std::endl;

    if(capture_data.size() > 0){
        pid_t p;
        std::string uri = capture_data[0]+",";
        std::cout << "URI " << uri  <<std::endl;

        fprintf(stderr, "About to spawn MEDIA process from pid %d\n", getpid());

        const char* args[] = {
            "./MEDIA",
            uri.c_str(),
            uri.c_str(),
            "MEDIAPID",
            nullptr,
            nullptr
        };

        int r = posix_spawn(&p, "./MEDIA", nullptr, nullptr,
                    (char**) args, nullptr);

        fprintf(stderr, "Child pid %d should run my MEDIA\n", p);

        char * MEDIAPID =(char*) malloc(6);
        sprintf(MEDIAPID, "%d", p);
    }
    
    return 0;
}
