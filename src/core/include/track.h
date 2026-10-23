#pragma once

#include <QString>
#include <QVector>
#include <QImage>
#include <QSet>
#include <taglib/fileref.h>

namespace metatag {

class Track {
public:
    Track() = default;
    explicit Track(const QString& filePath);

    bool load();
    bool save();

    QString filePath() const { return m_filePath; }
    QString artist() const { return m_artist; }
    QString album() const { return m_album; }
    QString title() const { return m_title; }
    int trackNumber() const { return m_trackNumber; }
    int discNumber() const { return m_discNumber; }
    QString genre() const { return m_genre; }
    int year() const { return m_year; }
    QString comment() const { return m_comment; }
    QString composer() const { return m_composer; }
    QString grouping() const { return m_grouping; }
    int bpm() const { return m_bpm; }
    QImage coverArt() const { return m_coverArt; }
    int duration() const { return m_duration; }
    bool isLoaded() const { return m_loaded; }
    bool isDirty() const { return m_dirty; }
    void setDirty(bool dirty = true) { m_dirty = dirty; }

    void setArtist(const QString& artist) { if (m_artist != artist) { m_artist = artist; m_modifiedFields.insert("artist"); m_dirty = true; } }
    void setAlbum(const QString& album) { if (m_album != album) { m_album = album; m_modifiedFields.insert("album"); m_dirty = true; } }
    void setTitle(const QString& title) { if (m_title != title) { m_title = title; m_modifiedFields.insert("title"); m_dirty = true; } }
    void setTrackNumber(int number) { if (m_trackNumber != number) { m_trackNumber = number; m_modifiedFields.insert("trackNumber"); m_dirty = true; } }
    void setDiscNumber(int number) { if (m_discNumber != number) { m_discNumber = number; m_modifiedFields.insert("discNumber"); m_dirty = true; } }
    void setGenre(const QString& genre) { if (m_genre != genre) { m_genre = genre; m_modifiedFields.insert("genre"); m_dirty = true; } }
    void setYear(int year) { if (m_year != year) { m_year = year; m_modifiedFields.insert("year"); m_dirty = true; } }
    void setComment(const QString& comment) { if (m_comment != comment) { m_comment = comment; m_modifiedFields.insert("comment"); m_dirty = true; } }
    void setComposer(const QString& composer) { if (m_composer != composer) { m_composer = composer; m_modifiedFields.insert("composer"); m_dirty = true; } }
    void setGrouping(const QString& grouping) { if (m_grouping != grouping) { m_grouping = grouping; m_modifiedFields.insert("grouping"); m_dirty = true; } }
    void setBpm(int bpm) { if (m_bpm != bpm) { m_bpm = bpm; m_modifiedFields.insert("bpm"); m_dirty = true; } }
    void setCoverArt(const QImage& cover) { m_coverArt = cover; m_dirty = true; m_coverArtModified = true; }
    void setDuration(int ms) { m_duration = ms; }

private:
    bool saveCoverArt(TagLib::FileRef& file, const QByteArray& imageData);
    bool removeCoverArt(TagLib::FileRef& file);
    bool loadCoverArt(TagLib::FileRef& file);

    QString m_filePath;
    QString m_artist;
    QString m_album;
    QString m_title;
    int m_trackNumber = 0;
    int m_discNumber = 0;
    QString m_genre;
    int m_year = 0;
    QString m_comment;
    QString m_composer;
    QString m_grouping;
    int m_bpm = 0;
    QImage m_coverArt;
    int m_duration = 0;
    bool m_loaded = false;
    bool m_dirty = false;
    bool m_coverArtModified = false;
    QSet<QString> m_modifiedFields;
};

}