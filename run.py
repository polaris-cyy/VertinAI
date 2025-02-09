import config, data_process, fixM4S, json, os

def main():
    parser = config.OptionParser()
    opt = parser.parse()
    if opt.move_data:
        data_process.move_data(opt.cache_path, opt.output_path)

    if opt.folder_operation:
        if opt.extract_frames:
            data_process.extract_frames_from_folder(opt.input_path, opt.output_path, opt.frame_interval, opt.num_threads)
        elif opt.fix:
            fixM4S.fixM4S_from_folder(opt.input_path, opt.output_path, opt.buf_size)
            fixM4S.modify_extension_from_folder(opt.input_path)
        elif opt.crop_video:
            data_process.video_crop_from_folder(opt.input_path, opt.output_path, opt.rewrite, opt.crop_size, opt.target_word, opt.num_threads)
        elif opt.merge:
            data_process.merge_audio_video_from_folder(opt.input_path, opt.output_path, opt.keep_audio, opt.keep_video)
    else:
        if opt.extract_frames:
            data_process.extract_frames(opt.input_path, opt.output_path, opt.frame_interval, opt.num_threads)
        elif opt.fix:
            fixM4S.fixM4S(opt.input_path, opt.output_path, opt.buf_size)
            fixM4S.modify_extension(opt.input_path)
        elif opt.crop_video:
            data_process.video_crop(opt.input_path, opt.output_path, opt.rewrite, opt.crop_size, opt.target_word, opt.num_threads)
    
    if opt.classify:
        ocr = None
        if opt.classifier == "paddleocr":
            from models.ocr import EasyOCR
            ocr = EasyOCR(opt)
        else:
            raise NotImplementedError("Classifier not implemented")
        
        ocr.find_index_by_word(opt.input_path, opt.target_word, opt.rewrite)
        data_process.calculate_audio_interval(opt.input_path, opt.rewrite)

    if opt.final_process:
        data_process.get_final_segment(opt.input_path, opt.rewrite, opt.expand, opt.video_frame_rate, opt.keep_audio, opt.keep_video, opt.language, opt)

    if opt.clear:
        data_process.clear(opt.input_path)

if __name__ == "__main__":
    main()