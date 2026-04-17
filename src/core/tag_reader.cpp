#include "tag_reader.h"
#include <taglib/fileref.h>
#include <taglib/tag.h>
#include <taglib/tpropertymap.h>
#include <taglib/flacfile.h>
#include <taglib/mp4file.h>
#include <taglib/mpegfile.h>
#include <taglib/vorbisfile.h>
#include <taglib/wavfile.h>
#include <taglib/aifffile.h>

namespace metatag {

Track TagReader::readTrack(const QString& filePath)
{
    Track track(filePath);
    track.load();
    return track;
}

QVector<Track> TagReader::readTracks(const QVector<QString>& filePaths)
{
    QVector<Track> tracks;
    tracks.reserve(filePaths.size());
    for (const auto& path : filePaths) {
        tracks.append(readTrack(path));
    }
    return tracks;
}

}