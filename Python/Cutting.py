import ffmpeg
import os

def cutVideo(timestamps: list, input_path: str, output_path: str):
    i = 0
    input_file = ffmpeg.input(input_path, f='mp4')
    clips = []

    in_file_probe_result = ffmpeg.probe(input_path)
    input_file_duration = in_file_probe_result.get(
        "format", {}).get("duration", None)

    if len(timestamps) == 0:
        output = ffmpeg.output(input_file, output_path)
    else:
        for timestamp in timestamps:
            # this section is based on:
            # https://github.com/CodingWith-Adam/trim-videos-with-ffmpeg-python/blob/main/app.py

            input_copy = input_file
            pts = "PTS-STARTPTS"

            #Shouldnt happen normaly but safety first
            """
            if float(input_file_duration) < timestamp[0]:
                timestamp[0] = input_file_duration
            if float(input_file_duration) < timestamp[1]:
                timestamp[1] = input_file_duration
            video_temp = (input_copy
                          .filter("atrim", start_pts=timestamp[0], end_pts=timestamp[1])
                          .filter("asetpts", pts)
                          #.label(f"test_video ${i}")
                          .filter_multi_output("split")
    
                          #.filter("split")
                          #.filter("merge_outputs")
              )
            """

            #video_temp = input_copy.trim(start_pts=timestamp[0], start_pts=timestamp[1]).setpts(pts)
            duration = int(timestamp[1]) - int(timestamp[0])
            video_temp = input_copy.trim(start=timestamp[0], end=timestamp[1], duration=duration).setpts(pts)
            audio_temp = (input_copy
                          .filter("atrim", start_pts=timestamp[0], end_pts=timestamp[1])
                          .filter("asetpts", pts)
                          #.label(f"test_audio ${i}")
                          .filter_multi_output("split")

                          #.filter("split")
                          #.filter("merge_outputs")
                          )
            #video_audio = ffmpeg.concat(video_temp.stream(), audio_temp.stream(), v=1, a=1, unsafe=True)
            video_audio = ffmpeg.concat(video_temp, audio_temp.stream(), v=1, a=1)
            video_audio.label = f"test${i}"
            #video_audio = ffmpeg.Stream(video_audio, upstream_label=f"test${i}",node_types=ffmpeg.nodes.FilterableStream.__name__)
            #video_audio = ffmpeg.output(ffmpeg.concat(video_temp, audio_temp, v=1, a=1, unsafe=True), "test.mp4")
            clips.append(video_audio)
            i += 1

        #out = ffmpeg.concat(*clips, v=1, a=1, unsafe=True)
        #output = ffmpeg.output(out.video, out.audio, output_path)
        output = ffmpeg.output(*clips, output_path)



        #out = ffmpeg.Stream(out, upstream_label=f"test${i +1}",node_types="FilterableNode")
        #output = ffmpeg.merge_outputs(ffmpeg.output(out, output_path))
        #output = ffmpeg.merge_outputs(ffmpeg.output(ffmpeg.concat(*clips).split().stream(), output_path))
        #output = ffmpeg.merge_outputs(out, output_path)


    #output = ffmpeg.merge_outputs(out.video, out.audio).stream(label=f"test${i + 1}")
    #final = ffmpeg.merge_outputs(output)
    #ffmpeg.probe(final)
    ffmpeg.run(output, capture_stdout=True, overwrite_output=True)


def getTimestamps(filepath):
    file = open(filepath, "r")
    timestamps = []

    for line in file:
        if line != "\n":
            split = line[:31]
            stamps = split.split(" --> ")
            startStamp = stamps[0][1:]
            if(startStamp.find(".")):
                startStamp=startStamp.split(".")[0]
            endStamp = stamps[1][:-1]
            if (endStamp.find(".")):
                endStamp = endStamp.split(".")[0]

            timestamps.append([startStamp, endStamp])

    return timestamps

def get_seconds(st):
    h, m, s = st.split(":")
    return int(h) * 3600 + int(m) * 60 + int(s)


def generateFfmpeg(timestamps: list, input_path:str, output_path:str):
    ffmpeg_timestamps = []
    for timestamp in timestamps:
        s = "between(t," + str(get_seconds(timestamp[0])) + "," + str(get_seconds(timestamp[1])) + ")" 
        ffmpeg_timestamps.append(s)

    #Video Stuff
    command = "ffmpeg -i " + input_path + " -vf \"select='"
    for ffmpeg_timestamp in ffmpeg_timestamps:
        command += ffmpeg_timestamp + "+"
    command = command[:-1] #remove the last +
    command += "', setpts=N/FRAME_RATE/TB\""

    #Audio Stuff
    command += " -af \"aselect='"
    for ffmpeg_timestamp in ffmpeg_timestamps:
        command += ffmpeg_timestamp + "+"
    command = command[:-1] #remove the last "+"
    command += "', asetpts=N/SR/TB\" " + output_path

    return command

def cutVideo(command: str):
    os.system(command)

if __name__ == '__main__':
    #test_timestamps = [[0, 10], [15, 20], [25, 50]]
    test_timestamps = getTimestamps(r"Videos_and_Audio/summary3.txt")
    input_path = r'Videos_and_Audio/HCI_Videos/HCI_3.mp4'
    output_path = 'HCI_3_Cut.mp4'
    command = generateFfmpeg(test_timestamps,input_path,output_path)
    print(command)
    cutVideo(command)


    #cutVideo(test_timestamps, input_path, output_path)
