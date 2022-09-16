#include <string>
#include <vector>
#include <cstdlib>
#include <sstream>
#include <cstring>
#include <spawn.h>
#include <iostream>
#include <algorithm>
#include "helpers.hh"

#include <bsoncxx/json.hpp>
#include <mongocxx/client.hpp>
#include <mongocxx/stdx.hpp>
#include <mongocxx/uri.hpp>
#include <mongocxx/instance.hpp>

#include <bsoncxx/builder/stream/helpers.hpp>
#include <bsoncxx/builder/stream/document.hpp>
#include <bsoncxx/builder/stream/array.hpp>

using bsoncxx::stdx::string_view;
using bsoncxx::builder::stream::document;
using bsoncxx::builder::stream::finalize;

using bsoncxx::builder::basic::kvp;
using bsoncxx::builder::basic::make_array;
using bsoncxx::builder::basic::make_document;

mongocxx::instance instance{};
mongocxx::uri uri("mongodb://192.168.0.51:27017");
mongocxx::client client(uri);
mongocxx::database db = client["photo_bomb"];

using namespace std;
mongocxx::collection _collection = db["live_cams"];
mongocxx::cursor cursor = _collection.find({});

#pragma once
#include <vector>
#include <iterator>

namespace Utils {
    template<typename InputIt, typename T = typename std::iterator_traits<InputIt>::value_type>
    std::vector<std::vector<T>> partition(InputIt first, InputIt last, unsigned size) {
        std::vector<std::vector<T>> result;
        std::vector<T>* batch{};
        for (unsigned index = 0, row = 0; first != last; ++first, ++index) {
            if ((index % size) == 0) {
                result.resize(++row);
                batch = &result.back();
                batch->reserve(size);
            }
            batch->push_back(*first);
        }
        return result;
    }
}

std::vector<std::string> capture_id = {};

 int main(){

    for(auto doc : cursor) {
        try{
            bsoncxx::document::element camera_ip = doc["camera_ip"];
            bsoncxx::document::element id = doc["_id"];
            bsoncxx::document::element channel = doc["channel_name"];
            bsoncxx::document::element camera_name = doc["cameraname"];
            bsoncxx::document::element stream_url = doc["camera_player"];
            //data for sample containers
            capture_id.push_back(id.get_oid().value.to_string());

        } catch (const std::exception& e){
            std::cout << e.what() << std::endl;
            std::cout << bsoncxx::to_json(doc) << "\n";
        }
    }


    // Split into sub groups
    auto namesPartition = Utils::partition(capture_id.begin(), capture_id.end(), 4);
    
    // Display grouped batches
    for (unsigned batchCount = 0; batchCount < namesPartition.size(); ++batchCount) {
        auto batch = namesPartition[batchCount];
        vector<string> channels;
        std::string channel;
        for (const auto& item : batch) {
            channel += item+",";
        }
        channels.push_back(channel);

        fprintf(stderr, "About to spawn MEDIA process from pid %d\n", getpid());

        pid_t p;

        const char* args[] = {
            "./MEDIA",
            channels[0].c_str(),
            channels[0].c_str(),
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
