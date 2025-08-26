from django.shortcuts import render
from django.http import JsonResponse, FileResponse
from pytubefix import Playlist, YouTube
import os
import threading

# Global dictionary to store download progress
progress_data = {}

def create_progress_callback(video_url):
    def progress_callback(stream, chunk, bytes_remaining):
        total_size = stream.filesize
        bytes_downloaded = total_size - bytes_remaining
        percentage = (bytes_downloaded / total_size) * 100
        progress_data[video_url] = percentage
    return progress_callback

def playlist_view(request):
    if request.method == 'POST':
        playlist_url = request.POST.get('playlist_url')
        if playlist_url:
            try:
                playlist = Playlist(playlist_url)
                videos = []
                for video_url in playlist.video_urls:
                    yt = YouTube(video_url)
                    resolutions = sorted(list(set([stream.resolution for stream in yt.streams.filter(progressive=True) if stream.resolution is not None])), key=lambda x: int(x[:-1]), reverse=True)
                    videos.append({
                        'title': yt.title,
                        'url': video_url,
                        'resolutions': resolutions
                    })
                return render(request, 'downloader/playlist.html', {'videos': videos, 'playlist_title': playlist.title})
            except Exception as e:
                return render(request, 'downloader/error.html', {'error_message': str(e)})
    return render(request, 'downloader/index.html')

def download_video(request):
    if request.method == 'POST':
        video_url = request.POST.get('video_url')
        playlist_title = request.POST.get('playlist_title')
        resolution = request.POST.get('resolution')

        if video_url and playlist_title and resolution:
            try:
                progress_callback = create_progress_callback(video_url)
                yt = YouTube(video_url, on_progress_callback=progress_callback)
                
                if resolution == 'highest':
                    stream = yt.streams.get_highest_resolution()
                else:
                    stream = yt.streams.filter(res=resolution, progressive=True).first()
                
                if not stream:
                    return JsonResponse({'success': False, 'message': f'No stream found for resolution {resolution}'})

                download_dir = os.path.join(os.path.expanduser('~'), 'Downloads', playlist_title)
                os.makedirs(download_dir, exist_ok=True)

                filename = stream.default_filename

                # Start download in a new thread
                thread = threading.Thread(target=stream.download, kwargs={'output_path': download_dir})
                thread.start()

                return JsonResponse({'success': True, 'message': 'Download started.', 'video_url': video_url, 'playlist_title': playlist_title, 'filename': filename})
            except Exception as e:
                return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'Invalid request.'})

def get_progress(request, video_url):
    percentage = progress_data.get(video_url, 0)
    return JsonResponse({'percentage': percentage})

def play_video(request):
    playlist_title = request.GET.get('playlist_title')
    filename = request.GET.get('filename')
    if playlist_title and filename:
        video_path = os.path.join(os.path.expanduser('~'), 'Downloads', playlist_title, filename)
        if os.path.exists(video_path):
            return FileResponse(open(video_path, 'rb'), as_attachment=False)
    return JsonResponse({'success': False, 'message': 'File not found.'})