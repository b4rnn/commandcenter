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

#include <string>
#include <cctype>
#include <sstream>
#include <fstream>
#include <algorithm> 

#include <sys/types.h>
#include <sys/stat.h>
#include <stdlib.h>

#include <opencv2/core.hpp>
#include <condition_variable>
#include <opencv2/opencv.hpp>
#include "opencv2/imgcodecs.hpp"

#include <sw/redis++/redis++.h>
#include <experimental/filesystem>

using namespace std;
using namespace cv;
using namespace sw::redis;
using namespace std::chrono_literals;

namespace fs = std::experimental::filesystem;

//class MTCNN;

/*REDIS*/
int face_count = 0;
//Redis *_redis = new Redis("tcp://127.0.0.1:6379");
Redis *_redis = new Redis("tcp://127.0.0.1:6379?keep_alive=true&socket_timeout=1000ms&connect_timeout=1000ms");

int main(int argc, char* argv[])
{

    vector<string> camera_data(argv, argv+argc);
    string text = camera_data[1];
    string delimiter = ",";
    vector<string> capture_data{};
    size_t pos = 0;
    while ((pos = text.find(delimiter)) != string::npos) {
        capture_data.push_back(text.substr(0, pos));
        text.erase(0, pos + delimiter.length());
    }
    
    //Width
    int frame_width = 1920; 
    //Height
    int frame_height = 1080;
    std::cout << " MEDIA CHANNEL ID " << capture_data[0] << " CAMERA ID " << capture_data[1]  << " CAMERA POSITION  " << capture_data[2]  << " CHANNEL SIZE " << capture_data[3]  <<" MARGIN LEFT " << capture_data[4]  <<" MARGIN TOP " << capture_data[5]  <<" HEIGHT  " << capture_data[6]  <<" WIDTH " << capture_data[7]  <<" SCREEN SIZE " << capture_data[3]  << " VECTOR SIZE " << capture_data.size() <<std::endl;
    if(capture_data.size() > 0){

        auto sub = _redis->subscriber();

        sub.on_message([&capture_data,frame_height,frame_width](std::string channel, std::string msg) {
             
            if(channel==capture_data[1]+"-cnc"){
                int pos = msg.find(":");
                std::string frame_raw_data = msg.substr(pos + 1);
                std::string frame_number =capture_data[4]+","+capture_data[5];
                std::vector<unsigned char> pic_data(frame_raw_data.begin(), frame_raw_data.end());
                cv::Mat vmat(pic_data, true);
                cv::Mat video_frame = cv::imdecode(vmat, 1);
                std::vector<uint8_t>* frame_buffer = new std::vector<uint8_t>(frame_width * frame_height * 3 + 16);
                cv::resize(video_frame, video_frame, Size(stoi(capture_data[6]), stoi(capture_data[7])), 0, 0, INTER_CUBIC);
                
                try{
                    cv::imencode(".png", video_frame, *frame_buffer);
                    std::string _data_payload((*frame_buffer).begin(), (*frame_buffer).end());
                    std::string data_payload = frame_number+":"+ _data_payload;
                    delete frame_buffer;
                    _redis->publish(capture_data[0]+"-"+capture_data[2], data_payload);
                    //std::cout << "CAMERA "<< capture_data[2] <<"-OF-CHANNEL-" << capture_data[3] << " WITH ID "<< capture_data[1] << " PIC DATA " << pic_data.size() <<" VMAT DATA " << vmat.size() << std::endl;
                    
                }catch( cv::Exception& e ){
                    const char* err_msg = e.what();
                    std::cout << "exception caught: corrrupted image on camera " << std::endl;
                }
                
            }
        });
        sub.subscribe({capture_data[1]+"-cnc"});
        sub.consume();
        
        // Consume messages in a loop.
        while (true) {
            try {
                sub.consume();
            } catch (...) {
                // Handle exceptions.
            }
        }

        sub.unsubscribe({capture_data[1]+"-cnc"});
        sub.consume();
    }

    return 0;
}
