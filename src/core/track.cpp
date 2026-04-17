#include "track.h"
#include <taglib/fileref.h>
#include <taglib/tag.h>
#include <taglib/tpropertymap.h>
#include <taglib/attachedpictureframe.h>
#include <taglib/id3v2tag.h>
#include <taglib/mpegfile.h>
#include <taglib/flacfile.h>
#include <taglib/mp4file.h>
#include <taglib/vorbisfile.h>
#include <taglib/wavfile.h>
#include <taglib/aifffile.h>
#include <taglib/flacpicture.h>
#include <taglib/mp4coverart.h>
#include <taglib/mp4item.h>
#include <taglib/oggfile.h>
#include <taglib/opusfile.h>
#include <taglib/xiphcomment.h>

#include <QImage>
#include <QBuffer>
#include <QDebug>

namespace metatag {

Track::Track(const QString& filePath)
    : m_filePath(filePath)
{
}

bool Track::load()
{
    m_loaded = false;
    TagLib::FileRef file(m_filePath.toStdString().c_str());
    if (file.isNull() || !file.tag())
        return false;

    TagLib::Tag *tag = file.tag();
    m_artist = QString::fromUtf8(tag->artist().toCString(true));
    m_album = QString::fromUtf8(tag->album().toCString(true));
    m_title = QString::fromUtf8(tag->title().toCString(true));
    m_trackNumber = tag->track();
    m_genre = QString::fromUtf8(tag->genre().toCString(true));
    m_year = tag->year();
    m_comment = QString::fromUtf8(tag->comment().toCString(true));

    // Extract additional fields from property map
    TagLib::PropertyMap props = file.file()->properties();
    if (props.contains("COMPOSER") && !props["COMPOSER"].isEmpty()) {
        m_composer = QString::fromUtf8(props["COMPOSER"].front().toCString(true));
    }
    if (props.contains("GROUPING") && !props["GROUPING"].isEmpty()) {
        m_grouping = QString::fromUtf8(props["GROUPING"].front().toCString(true));
    }
    if (props.contains("BPM") && !props["BPM"].isEmpty()) {
        m_bpm = props["BPM"].front().toInt();
    }
    if (props.contains("DISCNUMBER") && !props["DISCNUMBER"].isEmpty()) {
        m_discNumber = props["DISCNUMBER"].front().toInt();
    }

    // Try to extract cover art
    loadCoverArt(file);

    // Duration
    if (file.audioProperties()) {
        m_duration = file.audioProperties()->lengthInMilliseconds();
    }

    m_dirty = false;
    m_loaded = true;
    return true;
}

bool Track::loadCoverArt(TagLib::FileRef& file)
{
    // MP3/ID3v2
    if (TagLib::MPEG::File *mpegFile = dynamic_cast<TagLib::MPEG::File*>(file.file())) {
        if (mpegFile->ID3v2Tag()) {
            auto frames = mpegFile->ID3v2Tag()->frameList("APIC");
            if (!frames.isEmpty()) {
                auto *pic = static_cast<TagLib::ID3v2::AttachedPictureFrame*>(frames.front());
                QByteArray data(pic->picture().data(), pic->picture().size());
                return m_coverArt.loadFromData(data);
            }
        }
        return false;
    }

    // FLAC
    if (TagLib::FLAC::File *flacFile = dynamic_cast<TagLib::FLAC::File*>(file.file())) {
        auto pictureList = flacFile->pictureList();
        if (!pictureList.isEmpty()) {
            auto *pic = pictureList.front();
            QByteArray data(pic->data().data(), pic->data().size());
            return m_coverArt.loadFromData(data);
        }
        return false;
    }

    // MP4
    if (TagLib::MP4::File *mp4File = dynamic_cast<TagLib::MP4::File*>(file.file())) {
        if (mp4File->tag()) {
            auto coverList = mp4File->tag()->itemListMap()["covr"];
            if (!coverList.isEmpty()) {
                TagLib::MP4::CoverArt cover = coverList.toCoverArtList().front();
                QByteArray data(cover.data().data(), cover.data().size());
                return m_coverArt.loadFromData(data);
            }
        }
        return false;
    }

    // Ogg Vorbis
    if (TagLib::Ogg::Vorbis::File *vorbisFile = dynamic_cast<TagLib::Ogg::Vorbis::File*>(file.file())) {
        if (vorbisFile->tag()) {
            auto pictures = vorbisFile->tag()->pictureList();
            if (!pictures.isEmpty()) {
                auto *pic = pictures.front();
                QByteArray data(pic->data().data(), pic->data().size());
                return m_coverArt.loadFromData(data);
            }
        }
        return false;
    }

    // Ogg Opus
    if (TagLib::Ogg::Opus::File *opusFile = dynamic_cast<TagLib::Ogg::Opus::File*>(file.file())) {
        if (opusFile->tag()) {
            auto pictures = opusFile->tag()->pictureList();
            if (!pictures.isEmpty()) {
                auto *pic = pictures.front();
                QByteArray data(pic->data().data(), pic->data().size());
                return m_coverArt.loadFromData(data);
            }
        }
        return false;
    }

    return false;
}

bool Track::save()
{
    TagLib::FileRef file(m_filePath.toStdString().c_str(), true, TagLib::AudioProperties::Fast);
    if (file.isNull() || !file.tag())
        return false;

    TagLib::Tag *tag = file.tag();
    tag->setArtist(TagLib::String(m_artist.toUtf8().constData(), TagLib::String::UTF8));
    tag->setAlbum(TagLib::String(m_album.toUtf8().constData(), TagLib::String::UTF8));
    tag->setTitle(TagLib::String(m_title.toUtf8().constData(), TagLib::String::UTF8));
    tag->setTrack(m_trackNumber);
    tag->setGenre(TagLib::String(m_genre.toUtf8().constData(), TagLib::String::UTF8));
    tag->setYear(m_year);
    tag->setComment(TagLib::String(m_comment.toUtf8().constData(), TagLib::String::UTF8));

    // Update property map with additional fields
    TagLib::PropertyMap props = file.file()->properties();
    if (!m_composer.isEmpty()) {
        props["COMPOSER"] = TagLib::StringList(TagLib::String(m_composer.toUtf8().constData(), TagLib::String::UTF8));
    } else {
        props.erase("COMPOSER");
    }
    if (!m_grouping.isEmpty()) {
        props["GROUPING"] = TagLib::StringList(TagLib::String(m_grouping.toUtf8().constData(), TagLib::String::UTF8));
    } else {
        props.erase("GROUPING");
    }
    if (m_bpm > 0) {
        props["BPM"] = TagLib::StringList(TagLib::String(QString::number(m_bpm).toUtf8().constData(), TagLib::String::UTF8));
    } else {
        props.erase("BPM");
    }
    if (m_discNumber > 0) {
        props["DISCNUMBER"] = TagLib::StringList(TagLib::String(QString::number(m_discNumber).toUtf8().constData(), TagLib::String::UTF8));
    } else {
        props.erase("DISCNUMBER");
    }
    file.file()->setProperties(props);

    // Save cover art if present
    if (!m_coverArt.isNull()) {
        QByteArray bytes;
        QBuffer buffer(&bytes);
        buffer.open(QIODevice::WriteOnly);
        if (m_coverArt.save(&buffer, "PNG")) { // Use PNG for lossless
            if (!saveCoverArt(file, bytes)) {
                qWarning() << "Failed to save cover art";
            }
        } else {
            qWarning() << "Failed to encode cover art as PNG";
        }
    }

    bool ok = file.save();
    if (ok) {
        m_dirty = false;
    }
    return ok;
}

bool Track::saveCoverArt(TagLib::FileRef& file, const QByteArray& imageData)
{
    TagLib::ByteVector data(imageData.data(), imageData.size());

    // MP3/ID3v2
    if (TagLib::MPEG::File *mpegFile = dynamic_cast<TagLib::MPEG::File*>(file.file())) {
        auto *id3v2Tag = mpegFile->ID3v2Tag(true);
        if (!id3v2Tag) return false;
        id3v2Tag->removeFrames("APIC");
        auto *frame = new TagLib::ID3v2::AttachedPictureFrame;
        frame->setMimeType("image/png");
        frame->setPicture(data);
        id3v2Tag->addFrame(frame);
        return true;
    }

    // FLAC
    if (TagLib::FLAC::File *flacFile = dynamic_cast<TagLib::FLAC::File*>(file.file())) {
        auto *picture = new TagLib::FLAC::Picture;
        picture->setData(data);
        picture->setMimeType("image/png");
        picture->setType(TagLib::FLAC::Picture::FrontCover);
        flacFile->removePictures();
        flacFile->addPicture(picture);
        return true;
    }

    // MP4
    if (TagLib::MP4::File *mp4File = dynamic_cast<TagLib::MP4::File*>(file.file())) {
        TagLib::MP4::CoverArtList coverList;
        TagLib::MP4::CoverArt cover(TagLib::MP4::CoverArt::PNG, data);
        coverList.append(cover);
        mp4File->tag()->setItem("covr", TagLib::MP4::Item(coverList));
        return true;
    }

    // Ogg Vorbis
    if (TagLib::Ogg::Vorbis::File *vorbisFile = dynamic_cast<TagLib::Ogg::Vorbis::File*>(file.file())) {
        auto *picture = new TagLib::FLAC::Picture;
        picture->setData(data);
        picture->setMimeType("image/png");
        picture->setType(TagLib::FLAC::Picture::FrontCover);
        vorbisFile->tag()->removePictures();
        vorbisFile->tag()->addPicture(picture);
        return true;
    }

    // Ogg Opus
    if (TagLib::Ogg::Opus::File *opusFile = dynamic_cast<TagLib::Ogg::Opus::File*>(file.file())) {
        auto *picture = new TagLib::FLAC::Picture;
        picture->setData(data);
        picture->setMimeType("image/png");
        picture->setType(TagLib::FLAC::Picture::FrontCover);
        opusFile->tag()->removePictures();
        opusFile->tag()->addPicture(picture);
        return true;
    }

    // WAV (limited support)
    if (TagLib::RIFF::WAV::File *wavFile = dynamic_cast<TagLib::RIFF::WAV::File*>(file.file())) {
        // WAV files don't typically support embedded images in TagLib
        // Could potentially use ID3v2 if present, but WAV+ID3v2 is rare
        qWarning() << "Cover art saving not supported for WAV files";
        return false;
    }

    // AIFF (limited support)
    if (TagLib::RIFF::AIFF::File *aiffFile = dynamic_cast<TagLib::RIFF::AIFF::File*>(file.file())) {
        // Similar to WAV, AIFF doesn't typically support embedded images
        qWarning() << "Cover art saving not supported for AIFF files";
        return false;
    }

    qWarning() << "Cover art saving not supported for this file format";
    return false;
}

}