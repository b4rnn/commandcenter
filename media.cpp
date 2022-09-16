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
#include <sstream>
#include <fstream>
#include <algorithm> 

#include <ctime>
#include <sys/types.h>
#include <sys/stat.h>
#include <stdlib.h>

#include <opencv2/core.hpp>
#include <condition_variable>
#include <opencv2/opencv.hpp>
#include "opencv2/imgcodecs.hpp"

#include <sw/redis++/redis++.h>
#include <experimental/filesystem>

extern "C" {
#include <libavutil/opt.h>
#include <libavcodec/avcodec.h>
#include <libavutil/channel_layout.h>
#include <libavutil/common.h>
#include <libavutil/imgutils.h>
#include <libavutil/mathematics.h>
#include <libavutil/samplefmt.h>
#include <libavformat/avformat.h>
#include <libswscale/swscale.h>
#include <libswresample/swresample.h>
}

#include <bsoncxx/json.hpp>
#include <mongocxx/client.hpp>
#include <mongocxx/stdx.hpp>
#include <mongocxx/uri.hpp>
#include <mongocxx/instance.hpp>

#include <bsoncxx/builder/stream/helpers.hpp>
#include <bsoncxx/builder/stream/document.hpp>
#include <bsoncxx/builder/stream/array.hpp>

#include <bsoncxx/builder/basic/array.hpp>
#include <bsoncxx/builder/basic/document.hpp>
#include <bsoncxx/builder/basic/kvp.hpp>

#include <boost/thread.hpp>
#include <boost/thread/thread.hpp>
#include <boost/signals2/signal.hpp>
#include <boost/asio/io_service.hpp>

using namespace std;
using namespace cv;
using namespace sw::redis;
using namespace std::chrono_literals;

using bsoncxx::stdx::string_view;
using bsoncxx::builder::stream::document;
using bsoncxx::builder::stream::finalize;

using bsoncxx::builder::basic::kvp;
using bsoncxx::builder::basic::make_array;
using bsoncxx::builder::basic::make_document;

namespace fs = std::experimental::filesystem;

mongocxx::instance instance{};
mongocxx::uri uri("mongodb://127.0.0.1:27017");
mongocxx::client client(uri);
mongocxx::database db = client["photo_bomb"];

struct  boxing_face{
    string id;
    string key;
    string channel;
    StringView buffer;
    string frame_dimension;
};

boost::signals2::signal<void(string &msg)> sigDelete;

class XDELETE
{
  public :
    Redis *_redis = new Redis("tcp://127.0.0.1:6379?keep_alive=true&socket_timeout=100ms&connect_timeout=100ms");
    void operator()(string &msg) const
    {
        int pos = msg.find(":");
        std::string key = msg.substr(0 , pos);
        std::string id = msg.substr(pos + 1);
        //std::cout << "Hello, World!" << std::endl;
        std::cout << "Key............................... " << key <<" "<<"Id " << id << "\n";
        _redis->xdel(key, id);
    }
};

class MDELETE
{
  public :
    Redis *_redis = new Redis("tcp://127.0.0.1:6379?keep_alive=true&socket_timeout=100ms&connect_timeout=100ms");
    void operator()(string &msg) const
    {
        int pos = msg.find(":");
        std::string key = msg.substr(0 , pos);
        std::string id = msg.substr(pos + 1);
        //std::cout << "Hello, World!" << std::endl;
        std::cout << "Key " << key <<" "<<"Id " << id << "\n";
        _redis->xdel(key, id);
        //_redis->xgroup_delconsumer(key, "group", "consumer");
        //_redis->xgroup_destroy(key, "group");   
    }
};

class XDISPLAY
{
  public :
    Redis *_redis = new Redis("tcp://127.0.0.1:6379?keep_alive=true&socket_timeout=100ms&connect_timeout=100ms");
    void dee(std::string signal, std::string key){
        //sigDelete sig;
        if(signal=="START"){
            sigDelete.connect(XDELETE());
        }
        else{
            std::cout << "delete key " << key<< "\n";
           sigDelete(key);
        }
    }

    void operator()(boxing_face &buffer) const
    {
        std::unordered_map<std::string, StringView> _attrs = { {buffer.frame_dimension, buffer.buffer}};
        string _id = _redis->xadd(buffer.channel+"p-"+buffer.key.back(), "*", _attrs.begin(), _attrs.end());
        std::cout << "CamId " << buffer.channel <<" "<<"SreeamId " << buffer.id <<" "<<"Frame Dimension " << buffer.frame_dimension << " KEY " <<buffer.channel<<"p-"<<buffer.key.back() << "\n";
        std::string msg = buffer.key + ":" + buffer.id;
        XDISPLAY d;
        d.dee("",msg);
    }
};

int main(int argc, char* argv[])
{

    vector<string> camera_data(argv, argv+argc);
    camera_data.erase(camera_data.begin());

    string text = camera_data[1];
    string delimiter = ",";
    vector<string> capture_data{};

    size_t pos = 0;
    while ((pos = text.find(delimiter)) != string::npos) {
        capture_data.push_back(text.substr(0, pos));
        text.erase(0, pos + delimiter.length());
        std::cout << "getting bigger ?? " << capture_data.size() << std::endl;
    }

    //vector<string> capture_data(argv, argv+argc);
    //capture_data.erase(capture_data.begin());

    //find facial threshold
    /*
    auto _cursor = db["live_cams"].find(document{} 
        << "_id"
        << bsoncxx::oid{capture_data[0]}
        << finalize
    );

    std::string frame_rate;
    for(auto doc : _cursor) {
        bsoncxx::document::element FPS = doc["frame_rate"];
        frame_rate = FPS.get_utf8().value.to_string();
    }
    */
    std::string xid = capture_data[0];
    

    //Width
    int frame_width = 1920; 
    //Height
    int frame_height = 1080;
    //Frame Rate
    std::string frame_rate = "20";

    std::cout << "media ids " <<  xid  <<  " fps " << frame_rate << std::endl;

    cv::Mat* displayWindow = new cv::Mat(cv::Size(frame_width, frame_height),CV_8UC3 ,Scalar(0, 0, 0));

    using Attrs = std::vector<std::pair<std::string, std::string>>;
    using Item = std::pair<std::string, Optional<Attrs>>;
    using ItemStream = std::vector<Item>;
    
    boost::signals2::signal<void(string &msg)> sig;
    sig.connect(XDELETE());
    
    boost::signals2::signal<void(string &msg)> msig;
    msig.connect(MDELETE());
    
    boost::signals2::signal<void(boxing_face &buffer)> sigDisplay;
    sigDisplay.connect(XDISPLAY());

    XDISPLAY xd;
    xd.dee("START","");
    
    //DECODER
    if(capture_data.size() > 0){

         auto  CHANNEL = [frame_rate,frame_width,frame_height,&capture_data,displayWindow,&sigDisplay](const std::string& key){
            #pragma region
            string id = "0";
            string _id = "0";
            std::unordered_map<std::string,ItemStream > result;
            Redis *_redis = new Redis("tcp://127.0.0.1:6379?keep_alive=true&socket_timeout=100ms&connect_timeout=100ms");
            while(true){
                try{
                    _redis->xread(key, id, 1,std::inserter(result, result.end()));
                    if (!result.empty()) {
                        const auto &result_items = result.begin()->second;
                        auto &result_items_ = result.begin()->first;
                        auto count = result_items.size();
                        if( count > 0 ) {
                            for( size_t i = 0; i < count; ++i ) {
                                id = result_items[i].first;
                                _id = result_items_;
                                Optional<std::vector<std::pair<std::string, std::string>>> pvec = result_items[i].second;
                                for (std::pair<std::string, std::string> p : *pvec) {
                                    int pos = p.first.find(":");
                                    std::string w_h = p.first.substr(pos + 3);
                                    int _pos = w_h.find(":");
                                    std::string w_h_h_w = w_h.substr(0 , _pos);
                                    std::string w_h_w_h = w_h.substr(_pos + 1);
                                    int w_h_pos = w_h_w_h.find(":");
                                    std::string frame_dimension = p.first;
                                    std::string width  = w_h_w_h.substr(0 , w_h_pos);
                                    std::string height = w_h_w_h.substr(w_h_pos + 1);
                                    cv::Mat video_frame(stoi(height),stoi(width),CV_8UC3,p.second.data());

                                    std::cout << "CHANNEL THREAD ----------------- "<< frame_dimension << " WIDTH " << width << " HEIGHT " << height  << std::endl;
                                    
                                    StringView buffer ((char*)video_frame.ptr(), video_frame.total() * video_frame.channels());
                                    
                                    boxing_face BF ={id,key,capture_data[0],buffer,frame_dimension};
                                    sigDisplay(BF);
                                    
                                    /*
                                    std::unordered_map<std::string, StringView> _attrs = { {frame_dimension, buffer}};
                                    std::string _oid = _redis->xadd(capture_data[0]+"p-0", "*", _attrs.begin(), _attrs.end());
                                    std::string msg = key + ":" + id;
                                    sig(msg);
                                    std::cout << "CHANNEL THREAD ----------------- "<< frame_dimension << " WIDTH " << width << " HEIGHT " << height  << std::endl;
                                    */
                                }
                            }
                            result.erase(result.begin()); 
                        }
                    }

                } catch (const TimeoutError &e) {  
                    std::cout<< "SCREENS THREAD -----------------TIMEOUT ERROR "<<std::endl;
                        continue;
                }    
            }
            #pragma endregion
         };

        auto  _CHANNEL = [frame_rate,frame_width,frame_height,&capture_data,displayWindow,&msig](const std::string& key){
            Redis *_redis = new Redis("tcp://127.0.0.1:6379?keep_alive=true&socket_timeout=100ms&connect_timeout=100ms");
            try{
                av_register_all();
                avcodec_register_all();
                avformat_network_init();
                
                #pragma region
                std::string videoUrl  = capture_data[0];
                const char *outFname  = videoUrl.c_str();

                int directory_status,_directory_status;
                string folder_name = "/var/www/html/screens/"+capture_data[0];
                const char* dirname = folder_name.c_str();
                directory_status = mkdir(dirname,0777);

                auto Timestamps =  std::chrono::duration_cast<std::chrono::nanoseconds>
                (std::chrono::system_clock::now().time_since_epoch()).count();
                string sub_folder_name = folder_name+"/"+std::to_string(Timestamps);
                const char* _dirname = sub_folder_name.c_str();
                _directory_status =mkdir(_dirname,0777);
                std::cout << "CREATED DIR " <<  dirname << std::endl;

                std::string pktPos = key.c_str();
                std::string hls_segment_filename = sub_folder_name + "/"+"clip-"+pktPos.back()+"file%03d.ts";

                //std::string hls_segment_filename = sub_folder_name + "/0%05d.ts";
                std::cout << "HLS SEGMENT " <<  hls_segment_filename << std::endl;

                //ENCODER
                auto start = std::chrono::system_clock::now();

                AVFormatContext *format_ctx = avformat_alloc_context();
                std::string segment_list_type = sub_folder_name + "/stream.m3u8";

                avformat_alloc_output_context2(&format_ctx, nullptr,"hls", segment_list_type.c_str());
                if(!format_ctx) {
                    std::cout << "hls error "  << segment_list_type << std::endl;
                    return 1;
                }
            
                if (!(format_ctx->oformat->flags & AVFMT_NOFILE)) {
                    int avopen_ret  = avio_open2(&format_ctx->pb, outFname,
                                                AVIO_FLAG_WRITE, nullptr, nullptr);
                    if (avopen_ret < 0)  {
                        std::cout << "failed to open stream output context, stream will not work! " <<  outFname << std::endl;
                        return 1;
                    }
                }

                int _frame_rate = 64;
                AVCodec *out_codec = avcodec_find_encoder(AV_CODEC_ID_H264);
                AVStream *out_stream = avformat_new_stream(format_ctx, out_codec);
                AVCodecContext *out_codec_ctx = avcodec_alloc_context3(out_codec);
                //set codec params
                //const AVRational dst_fps = {stoi(frame_rate), 1};
                const AVRational dst_fps = {_frame_rate, 1};
                out_codec_ctx->codec_tag = 0;
                out_codec_ctx->codec_id = AV_CODEC_ID_H264;
                out_codec_ctx->codec_type = AVMEDIA_TYPE_VIDEO;
                out_codec_ctx->width = frame_width;
                out_codec_ctx->height = frame_height;
                out_codec_ctx->gop_size = 3*stoi(frame_rate)*4;
                out_codec_ctx->bit_rate = 50000;
                out_codec_ctx->pix_fmt = AV_PIX_FMT_YUV420P;
                out_codec_ctx->framerate = dst_fps;
                //out_codec_ctx->skip_frame = AVDISCARD_BIDIR;
                out_codec_ctx->time_base.num = 1;
                //out_codec_ctx->time_base.den = 3;
                out_codec_ctx->time_base.den = _frame_rate; // fps
                //out_codec_ctx->time_base.den = stoi(frame_rate); // fps
                out_codec_ctx->thread_count = 4;
                out_codec_ctx->thread_type = FF_THREAD_SLICE;

                if (format_ctx->oformat->flags & AVFMT_GLOBALHEADER)
                {
                    out_codec_ctx->flags |= AV_CODEC_FLAG_GLOBAL_HEADER;
                }

                int ret_avp = avcodec_parameters_from_context(out_stream->codecpar, out_codec_ctx);
                if (ret_avp < 0)
                {
                    std::cout << "Could not initialize stream codec parameters!" << std::endl;
                    exit(1);
                }


                int av_ret;
                int frames_validator;
                int frames_counter = 0;
                AVFrame *frame = av_frame_alloc();
                std::vector<uint8_t>* imgbuf = new std::vector<uint8_t>(frame_height * frame_width * 3 + 16);
                std::vector<uint8_t>* framebuf = new std::vector<uint8_t>(av_image_get_buffer_size(AV_PIX_FMT_YUV420P, frame_width, frame_height, 1));
                cv::Mat* image = new cv::Mat(frame_height, frame_width, CV_8UC3, imgbuf->data(), frame_width * 3);

                #pragma endregion
                    
                if (!_directory_status){

                    #pragma region
                    //update dp
                    auto end = std::chrono::system_clock::now();
                    std::chrono::duration<double> elapsed_seconds = end-start;
                    std::time_t end_time = std::chrono::system_clock::to_time_t(end);

                    std::ostringstream oss;
                    oss << std::ctime(&end_time);
                    auto timestamp = oss.str();

                    std::istringstream iss(timestamp);

                    std::vector<std::string> captured_time{istream_iterator<std::string>{iss},istream_iterator<std::string>{}};

                    //Get Time
                    std::time_t Dtime;
                    std::tm* Tinfo;
                    char Tbuffer [80];

                    std::time(&Dtime);
                    Tinfo = std::localtime(&Dtime);

                    std::strftime(Tbuffer,80,"%Y-%m-%d:%H:%M:%S",Tinfo);
                    std::puts(Tbuffer);
                    string _time(Tbuffer);
                    
                    db["screen_recordings"].insert_one(document{} 
                        << "camera_id"      <<  capture_data[0]
                        << "recording_id"   <<  std::to_string(Timestamps)
                        << "time"           <<  _time
                        << "recording_time" <<  timestamp
                        << "time_day"       <<  captured_time[0]
                        << "time_month"     <<  captured_time[1]
                        << "time_date"      <<  captured_time[2]
                        << "time_year"      <<  captured_time[4]
                        << "time_score"     <<  std::to_string(Timestamps)
                        << "recording_url"  <<  segment_list_type.erase(0,13)
                        << "utc_time"       <<  bsoncxx::types::b_date(std::chrono::system_clock::now())
                        << finalize
                    );

                    bsoncxx::stdx::optional<bsoncxx::document::value> maybe_result = db["screens"].find_one(document{} << "screen_id" << bsoncxx::oid{capture_data[0]} << finalize);
                    if(maybe_result) {
                        std::cout << bsoncxx::to_json(*maybe_result) << "\n";
                        db["screens"].update_one(document{} << "screen_id" << bsoncxx::oid{capture_data[0]}<< finalize,
                            document{}<<"$set" << bsoncxx::builder::stream::open_document <<"screens_player"
                            << segment_list_type << bsoncxx::builder::stream::close_document
                            <<finalize
                        );
                    }else{

                    db["screens"].insert_one(document{} 
                        << "screen_id"      <<  bsoncxx::oid{capture_data[0]} 
                        << "screens_player"      <<  segment_list_type
                        << finalize
                        );
                    }
                    
                    AVDictionary *hlsOptions = NULL;
                    av_dict_set(&hlsOptions, "profile", "baseline", 0);
                    av_dict_set(&hlsOptions, "c", "copy", 0);
                    av_dict_set(&hlsOptions, "preset", "ultrafast", 0);
                    av_dict_set(&hlsOptions, "tune", "zerolatency", 0);
                    av_dict_set(&hlsOptions, "x264encopts", "slow_firstpass:ratetol=100", 0);
                    av_dict_set(&hlsOptions, "pass", "2", 0);
                    av_dict_set(&hlsOptions, "strict", "-4", 0);
                    av_dict_set(&hlsOptions, "crf", "28", 0); 
                    av_dict_set(&hlsOptions, "force_key_frames", "expr:gte(t,n_forced*18)", AV_DICT_DONT_OVERWRITE);

                    av_dict_set(&hlsOptions, "hls_segment_type",   "mpegts", 0);
                    av_dict_set(&hlsOptions, "segment_list_type",  "m3u8",   0);
                    av_dict_set(&hlsOptions, "hls_segment_filename", hls_segment_filename.c_str(),   0);
                    av_dict_set(&hlsOptions, "g",frame_rate.c_str(), 0);
                    av_dict_set(&hlsOptions, "hls_time",   "1", 0);
                    av_dict_set(&hlsOptions, "hls_list_size",   "0", 0);
                    //av_dict_set(&hlsOptions,     "hls_playlist_type", "vod", 0);
                    av_dict_set(&hlsOptions,     "segment_time_delta", "1.0", 0);
                    //av_dict_set(&hlsOptions,     "hls_flags", "append_list", 0);
                    av_dict_set_int(&hlsOptions, "reference_stream",   out_stream->index, 0);
                    //av_dict_set(&hlsOptions, "segment_list_flags", "cache+live", 0);

                    int ret_avo = avcodec_open2(out_codec_ctx, out_codec, &hlsOptions);
                    
                    if (ret_avo < 0)
                    {
                        std::cout << "Could not open video encoder!" << std::endl;
                        exit(1);
                    }
                    out_stream->codecpar->extradata = out_codec_ctx->extradata;
                    out_stream->codecpar->extradata_size = out_codec_ctx->extradata_size;

                    av_dump_format(format_ctx, 0, outFname, 1);

                    SwsContext * pSwsCtx = sws_getContext(frame_width,frame_height,AV_PIX_FMT_BGR24, frame_width, frame_height , AV_PIX_FMT_YUV420P , SWS_FAST_BILINEAR, NULL, NULL, NULL);
                            
                    if (pSwsCtx == NULL) {
                        fprintf(stderr, "Cannot initialize the sws context\n");
                        exit(1);
                        return -1;
                    }
                    

                    int ret_avfw = avformat_write_header(format_ctx, &hlsOptions);
                    if (ret_avfw < 0)
                    {
                        std::cout << "Could not write header!" << std::endl;
                        exit(1);
                    }
                    #pragma endregion

                    #pragma region

                    string id = "0";
                    string _id = "0";
                    std::string  cam_1_key = key + "-0";
                    std::string  cam_2_key = key + "-1";
                    std::string  cam_3_key = key + "-2";
                    std::string  cam_4_key = key + "-3";
                    std::unordered_map<std::string,ItemStream > result;

                    while(true){
                        try{
                            std::unordered_map<std::string, std::string> keys = { {cam_1_key, id}, {cam_2_key, id},{cam_3_key, id},{cam_4_key, id}};
                            _redis->xread(keys.begin(), keys.end(), 10, std::inserter(result, result.end()));
                            if (!result.empty()) {
                                const auto &result_items = result.begin()->second;
                                auto &result_items_ = result.begin()->first;
                                auto count = result_items.size();
                                if( count > 0 ) {
                                    for( size_t i = 0; i < count; ++i ) {
                                        id = result_items[i].first;
                                        _id = result_items_;
                                        Optional<std::vector<std::pair<std::string, std::string>>> pvec = result_items[i].second;
                                        for (std::pair<std::string, std::string> p : *pvec) {
                                            int pos = p.first.find(":");
                                            std::string MarginLeft = p.first.substr(0 , pos);
                                            std::string _MarginTop = p.first.substr(pos + 1);
                                            int tpos = _MarginTop.find(":");
                                            std::string MarginTop  = _MarginTop.substr(0 ,tpos);
                                            std::string w_h = p.first.substr(pos + 3);
                                            int _pos = w_h.find(":");
                                            std::string w_h_h_w = w_h.substr(0 , _pos);
                                            std::string w_h_w_h = w_h.substr(_pos + 1);
                                            int w_h_pos = w_h_w_h.find(":");
                                            std::string frame_dimension = p.first;
                                            std::string width  = w_h_w_h.substr(0 , w_h_pos);
                                            std::string height = w_h_w_h.substr(w_h_pos + 1);
                                            
                                            cv::Mat video_frame(stoi(height),stoi(width),CV_8UC3,p.second.data()); 
                                            (&video_frame)->copyTo((*image)(cv::Rect(stoi(MarginLeft),stoi(MarginTop),(&video_frame)->cols, (&video_frame)->rows )));

                                            std::cout<< "MEDIA THREAD ----------------- " << id << " " <<p.first<< " " << _id << " FOLDER " << segment_list_type << " WIDTH " << width << " HEIGHT " << height << " MarginTop " << MarginTop << " MarginLeft " << MarginLeft <<std::endl;
            
                                            av_image_fill_arrays(frame->data, frame->linesize, framebuf->data(), AV_PIX_FMT_YUV420P, frame_width, frame_height, 1);
                                            frame->width = frame_width;
                                            frame->height = frame_height;
                                            frame->format = static_cast<int>(AV_PIX_FMT_YUV420P);
                                            
                                            //*image = video_frame;

                                            const int stride[] = {static_cast<int>(image->step[0])};
                                            sws_scale(pSwsCtx, &image->data, stride , 0 , frame_height , frame->data, frame->linesize); 
                                            frame->pts += av_rescale_q(1, out_codec_ctx->time_base, out_stream->time_base);

                                            std::cout <<frame->pts << " WIDTH " <<  frame->width <<" HEIGHT " << frame->height << " LENGTH "<< p.second.length() << " FOLDER " << segment_list_type << std::endl;
                                            
                                            AVPacket pkt = {0};
                                            av_init_packet(&pkt);

                                            if(out_stream != NULL){
                                                
                                                int ret_frame = avcodec_send_frame(out_codec_ctx, frame);
                                                if (ret_frame < 0)
                                                {
                                                    std::cout << "Error sending frame to codec context!" << std::endl;
                                                    exit(1);
                                                }
                                                int ret_pkt = avcodec_receive_packet(out_codec_ctx, &pkt);
                                                if (ret_pkt < 0)
                                                {
                                                    std::cout << "Error receiving packet from codec context!" << " WIDTH " <<  frame_width <<" HEIGHT " << frame_height << std::endl;
                                                    exit(1);
                                                }

                                                if (pkt.pts == AV_NOPTS_VALUE || pkt.dts == AV_NOPTS_VALUE) {
                                                    av_log (format_ctx, AV_LOG_ERROR,
                                                        "Timestamps are unset in a packet for stream% d\n", out_stream-> index);
                                                    return AVERROR (EINVAL);
                                                    exit(1);
                                                }

                                                if (pkt.pts < pkt.dts) {
                                                    av_log (format_ctx, AV_LOG_ERROR, "pts%" PRId64 "<dts%" PRId64 "in stream% d\n",
                                                    pkt.pts, pkt.dts,out_stream-> index);
                                                    return AVERROR (EINVAL);
                                                    exit(1);
                                                }
                                                if (pkt.stream_index == out_stream->index){
                                                    av_interleaved_write_frame(format_ctx, &pkt);
                                                }
                                            }
                                            
                                            std::string msg = _id + ":" + id;
                                            msig(msg);
                                        }
                                    }
                                    result.erase(result.begin()); 
                                }
                            } 
                        } catch (const TimeoutError &e) {  
                            std::cout<< "MEDIA THREAD -----------------TIMEOUT ERROR "<<std::endl;
                            continue;
                        }            
                    }
                    #pragma endregion
                    av_frame_unref(frame);
                } 
            } catch (const Exception &evr) {  
                const char* err_msg = evr.what();
                std::cout<< "MEDIA THREAD -----------------XGROUP ERROR "<<std::endl;
                //continue;
            }   
        };

        thread t1(std::thread(CHANNEL,  capture_data[0]+"-0"));
        thread t2(std::thread(CHANNEL,  capture_data[0]+"-1"));
        thread t3(std::thread(CHANNEL,  capture_data[0]+"-2"));
        thread t4(std::thread(CHANNEL,  capture_data[0]+"-3"));
        thread t5(std::thread(_CHANNEL, capture_data[0]+"p"));
        XDELETE xdelete;
        string s="DELETE USED FILES";
        boost::thread t7((XDELETE()),boost::move(s));
        MDELETE mdelete;
        string m="DELETE USED FILES";
        boost::thread t8((MDELETE()),boost::move(m));
        boxing_face d ={"a-a-a-a","b-b-b-b","c-c-c-c","d-d-d-d","f-f-f-f"};
        boost::thread t9((XDISPLAY()),boost::move(d));
        
        t1.join();
        t2.join();
        t3.join();
        t4.join();
        t5.join();
        t7.join();
        t8.join();
        t9.join();
    }
    
    return 0;
}
