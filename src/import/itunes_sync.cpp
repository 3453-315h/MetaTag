#include "itunes_sync.h"
#include "track.h"
#include <QFile>
#include <QXmlStreamReader>
#include <QDebug>
#include <QUrl>

namespace metatag {

static bool parseTracksDict(QXmlStreamReader& xml, QVector<Track>& tracks)
{
    while (xml.readNextStartElement()) {
        if (xml.name() == QStringLiteral("key")) {
            // Track ID
            xml.readElementText();
            if (xml.readNextStartElement() && xml.name() == QStringLiteral("dict")) {
                QString location;
                QString artist, album, title, genre, composer, grouping, comment;
                int trackNumber = 0, discNumber = 0, year = 0, bpm = 0;

                while (xml.readNextStartElement()) {
                    if (xml.name() == QStringLiteral("key")) {
                        QString key = xml.readElementText();
                        if (xml.readNextStartElement()) {
                            QString valText = xml.readElementText();

                            if (key == QStringLiteral("Location")) {
                                QUrl url(valText);
                                location = url.isLocalFile() ? url.toLocalFile() : url.path();
#ifdef Q_OS_WIN
                                if (location.startsWith('/') && location.length() > 2 && location[2] == ':') {
                                    location = location.mid(1);
                                }
#endif
                            } else if (key == QStringLiteral("Artist")) {
                                artist = valText;
                            } else if (key == QStringLiteral("Album")) {
                                album = valText;
                            } else if (key == QStringLiteral("Name")) {
                                title = valText;
                            } else if (key == QStringLiteral("Genre")) {
                                genre = valText;
                            } else if (key == QStringLiteral("Composer")) {
                                composer = valText;
                            } else if (key == QStringLiteral("Grouping")) {
                                grouping = valText;
                            } else if (key == QStringLiteral("Comments")) {
                                comment = valText;
                            } else if (key == QStringLiteral("Track Number")) {
                                trackNumber = valText.toInt();
                            } else if (key == QStringLiteral("Disc Number")) {
                                discNumber = valText.toInt();
                            } else if (key == QStringLiteral("Year")) {
                                year = valText.toInt();
                            } else if (key == QStringLiteral("BPM")) {
                                bpm = valText.toInt();
                            }
                        }
                    } else {
                        xml.skipCurrentElement();
                    }
                }

                if (!location.isEmpty()) {
                    Track track(location);
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
            } else {
                xml.skipCurrentElement();
            }
        } else {
            xml.skipCurrentElement();
        }
    }

    return !xml.hasError();
}

bool iTunesSync::importLibrary(const QString& xmlPath, QVector<Track>& tracks)
{
    QFile file(xmlPath);
    if (!file.open(QIODevice::ReadOnly | QIODevice::Text)) {
        qWarning() << "Failed to open iTunes library XML:" << xmlPath;
        return false;
    }

    QXmlStreamReader xml(&file);

    while (xml.readNextStartElement()) {
        if (xml.name() == QStringLiteral("plist")) {
            while (xml.readNextStartElement()) {
                if (xml.name() == QStringLiteral("dict")) {
                    while (xml.readNextStartElement()) {
                        if (xml.name() == QStringLiteral("key")) {
                            QString key = xml.readElementText();
                            if (key == QStringLiteral("Tracks")) {
                                if (xml.readNextStartElement() && xml.name() == QStringLiteral("dict")) {
                                    if (!parseTracksDict(xml, tracks))
                                        return false;
                                }
                            } else {
                                if (xml.readNextStartElement()) {
                                    xml.skipCurrentElement();
                                }
                            }
                        } else {
                            xml.skipCurrentElement();
                        }
                    }
                } else {
                    xml.skipCurrentElement();
                }
            }
        } else {
            xml.skipCurrentElement();
        }
    }

    if (xml.hasError()) {
        qWarning() << "XML error:" << xml.errorString();
        return false;
    }

    file.close();
    return true;
}

bool iTunesSync::exportChanges(const QVector<Track>& tracks)
{
    qWarning() << "iTunes export is not implemented. Changes were not exported to iTunes library.";
    return false;
}

} // namespace metatag