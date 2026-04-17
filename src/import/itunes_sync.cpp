#include "itunes_sync.h"
#include "track.h"
#include <QFile>
#include <QXmlStreamReader>
#include <QDebug>
#include <QUrl>

namespace metatag {

static bool parseTracksDict(QXmlStreamReader& xml, QVector<Track>& tracks);

bool iTunesSync::importLibrary(const QString& xmlPath, QVector<Track>& tracks)
{
    QFile file(xmlPath);
    if (!file.open(QIODevice::ReadOnly | QIODevice::Text)) {
        qWarning() << "Failed to open iTunes library XML:" << xmlPath;
        return false;
    }
    
    QXmlStreamReader xml(&file);
    
    while (!xml.atEnd() && !xml.hasError()) {
        xml.readNext();
        if (xml.isStartElement() && xml.name() == QStringLiteral("plist")) {
            // Read plist contents
            while (!xml.atEnd() && !xml.hasError()) {
                xml.readNext();
                if (xml.isEndElement() && xml.name() == QStringLiteral("plist"))
                    break;
                if (xml.isStartElement() && xml.name() == QStringLiteral("dict")) {
                    // Parse top-level dict
                    while (!xml.atEnd() && !xml.hasError()) {
                        xml.readNext();
                        if (xml.isEndElement() && xml.name() == QStringLiteral("dict"))
                            break;
                        if (xml.isStartElement() && xml.name() == QStringLiteral("key")) {
                            QString key = xml.readElementText();
                            if (key == QStringLiteral("Tracks")) {
                                xml.readNext(); // start of dict
                                if (xml.isStartElement() && xml.name() == QStringLiteral("dict")) {
                                    if (!parseTracksDict(xml, tracks))
                                        return false;
                                }
                            } else {
                                // Skip value
                                xml.readNext();
                                if (xml.isStartElement() && xml.name() == QStringLiteral("dict")) {
                                    // skip entire dict
                                    int depth = 1;
                                    while (depth > 0 && !xml.atEnd() && !xml.hasError()) {
                                        xml.readNext();
                                        if (xml.isStartElement())
                                            depth++;
                                        else if (xml.isEndElement())
                                            depth--;
                                    }
                                } else if (xml.isStartElement()) {
                                    xml.skipCurrentElement();
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    if (xml.hasError()) {
        qWarning() << "XML error:" << xml.errorString();
        return false;
    }
    
    file.close();
    return true;
}

static bool parseTracksDict(QXmlStreamReader& xml, QVector<Track>& tracks)
{
    while (!xml.atEnd() && !xml.hasError()) {
        xml.readNext();
        if (xml.isEndElement() && xml.name() == QStringLiteral("dict"))
            break;
        
        if (xml.isStartElement() && xml.name() == QStringLiteral("key")) {
            QString trackId = xml.readElementText(); // track ID, ignore
            xml.readNext(); // start of dict
            if (xml.isStartElement() && xml.name() == QStringLiteral("dict")) {
                // parse track properties
                QString location;
                QString artist, album, title, genre, composer, grouping, comment;
                int trackNumber = 0, discNumber = 0, year = 0, bpm = 0;
                
                while (!xml.atEnd() && !xml.hasError()) {
                    xml.readNext();
                    if (xml.isEndElement() && xml.name() == QStringLiteral("dict"))
                        break;
                    if (xml.isStartElement() && xml.name() == QStringLiteral("key")) {
                        QString key = xml.readElementText();
                        xml.readNext(); // value
                        if (xml.isCharacters() || xml.isStartElement()) {
                            QString value;
                            if (xml.isCharacters())
                                value = xml.text().toString();
                            else if (xml.isStartElement() && xml.name() == QStringLiteral("string"))
                                value = xml.readElementText();
                            
                            if (key == QStringLiteral("Location"))
                                location = QUrl(value).toLocalFile();
                            else if (key == QStringLiteral("Artist"))
                                artist = value;
                            else if (key == QStringLiteral("Album"))
                                album = value;
                            else if (key == QStringLiteral("Name"))
                                title = value;
                            else if (key == QStringLiteral("Genre"))
                                genre = value;
                            else if (key == QStringLiteral("Composer"))
                                composer = value;
                            else if (key == QStringLiteral("Grouping"))
                                grouping = value;
                            else if (key == QStringLiteral("Comments"))
                                comment = value;
                            else if (key == QStringLiteral("Track Number"))
                                trackNumber = value.toInt();
                            else if (key == QStringLiteral("Disc Number"))
                                discNumber = value.toInt();
                            else if (key == QStringLiteral("Year"))
                                year = value.toInt();
                            else if (key == QStringLiteral("BPM"))
                                bpm = value.toInt();
                        }
                        // skip remaining elements
                        if (xml.isStartElement())
                            xml.skipCurrentElement();
                    }
                }
                
                if (!location.isEmpty()) {
                    // Convert location to local path (remove URL encoding and file://)
                    QString filePath = QUrl(location).toLocalFile();
                    if (!filePath.isEmpty()) {
                        Track track(filePath);
                        if (track.load()) {
                            if (!artist.isEmpty())
                                track.setArtist(artist);
                            if (!album.isEmpty())
                                track.setAlbum(album);
                            if (!title.isEmpty())
                                track.setTitle(title);
                            if (!genre.isEmpty())
                                track.setGenre(genre);
                            if (!composer.isEmpty())
                                track.setComposer(composer);
                            if (!grouping.isEmpty())
                                track.setGrouping(grouping);
                            if (!comment.isEmpty())
                                track.setComment(comment);
                            if (trackNumber > 0)
                                track.setTrackNumber(trackNumber);
                            if (discNumber > 0)
                                track.setDiscNumber(discNumber);
                            if (year > 0)
                                track.setYear(year);
                            if (bpm > 0)
                                track.setBpm(bpm);
                            
                            tracks.append(track);
                        }
                    }
                }
            }
        }
    }
    
    return !xml.hasError();
}

bool iTunesSync::exportChanges(const QVector<Track>& tracks)
{
    // For now, just log that this is not implemented
    // A full implementation would need to:
    // 1. Read the existing iTunes XML
    // 2. Update track entries with new metadata
    // 3. Write back the XML
    // This is complex and error-prone, so we'll leave it unimplemented for now

    qWarning() << "iTunes export is not implemented. Changes were not exported to iTunes library.";
    return false;
}

}