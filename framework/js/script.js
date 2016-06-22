var channelName = 'whitehatcalpoly';

$(document).ready(function(){
    $.get(
        "https://www.googleapis.com/youtube/v3/channels", {
            part: 'contentDetails',
            forUsername: channelName,
            key: 'AIzaSyA0OzE8K3nQt6SuHlbwniUH6B3CFu15eTU'},
            function(data) {
                $.each(data.items, function(i, item) {
                    console.log(item);
                    playlistID = item.contentDetails.relatedPlaylists.uploads;
                    getVideos(playlistID);
                })
            }
    );
    
    function getVideos() {
         $.get(
        "https://www.googleapis.com/youtube/v3/playlistItems", {
            part: 'snippet',
            maxResults: 10,
            playlistID: playlistID,
            key: 'AIzaSyA0OzE8K3nQt6SuHlbwniUH6B3CFu15eTU'},
            function(data) {
                var output;
                $.each(data.items, function(i, item) {
                    console.log(item);
                    videoTitle = item.snippet.title;
                    
                    output = '<li>' + videoTitle + '<li>'
                    $('#results').append(output);
                })
            }
    ); 
    };
});