import config, data_process, fixM4S

def main():
    parser = config.OptionParser()
    opt = parser.parse()

    if opt.move_data:
        data_process.move_data(opt.cache_path, opt.output_path)

    if opt.file_operation:
        if opt.extract_frames:
            data_process.extract_frames_from_folder(opt.input_path, opt.output_path, opt.frame_interval, opt.num_threads)
        elif opt.compress_video:
            data_process.video_compress_from_folder(opt.input_path, opt.output_path, opt.frame_rate,opt.rewrite, opt.high_quality, opt.num_threads)
        elif opt.fix:
            fixM4S.fixM4S_from_folder(opt.input_path, opt.output_path, opt.buf_size)
            fixM4S.modify_extension_from_folder(opt.input_path)
        elif opt.crop_video:
            data_process.video_crop_from_folder(opt.input_path, opt.output_path, opt.rewrite, opt.crop_size, opt.num_threads)
    else:
        if opt.extract_frames:
            data_process.extract_frames(opt.input_path, opt.output_path, opt.frame_interval, opt.num_threads)
        elif opt.compress_video:
            data_process.video_compress(opt.input_path, opt.output_path, opt.frame_rate, opt.rewrite, opt.high_quality, opt.num_threads)
        elif opt.fix:
            fixM4S.fixM4S(opt.input_path, opt.output_path, opt.buf_size)
            fixM4S.modify_extension(opt.input_path)
        elif opt.crop_video:
            data_process.video_crop(opt.input_path, opt.output_path, opt.rewrite, opt.crop_size, opt.num_threads)
    
    if opt.classify:
        ocr = None
        if opt.classifier == "paddleocr":
            from models.ocr import EasyOCR
            ocr = EasyOCR()
        ocr.find_index_by_word(opt.input_path, opt.target_word, opt.match_threshold, opt.rewrite)
        data_process.calculate_audio_interval(opt.input_path, opt.rewrite)
    if opt.final_process:
        data_process.get_final_segment(opt.input_path, opt.rewrite, opt.expand, opt.video_frame_rate, opt.keep_audio, opt.keep_video, opt.language)

    if opt.clear:
        data_process.clear(opt.input_path)

if __name__ == "__main__":
    main()