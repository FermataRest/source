// (hookshot) Which textures were destroyed, by their creation number (Texture::id), apart from Vulkan so that
// tests/test_texture_gone.py can run it.
//
// A texture pointer kept from one draw to a later one (vk_temporal.cpp: the scene's colour and depth from the scene's draws
// to the engine's pass, the upscale's output from one frame's dispatch to the next frame's tone mapping) has to be known
// to be the same texture still. texture_destroy_generation says only that some texture went since, anywhere: with the video
// memory full the cache lets textures go in most frames, and each of those frames then lost the engine's picture (the tone
// mapping was not drawn at the output's size, and the frame was the scene's size scaled up: a soft frame, some every second
// on an 8 GB card at 2560x1440). This says whether that one texture went.
#pragma once

#include <cstdint>
#include <mutex>

namespace texture_gone {

/// The creation numbers of the textures destroyed last, and how many went in all. A texture noted while it was there (its
/// number, and count() then) is there still while its number is not among those that went since. When more went since than
/// are kept, or the number is none (0), it cannot be told: it counts as gone, which costs a frame what the old rule cost it
class Record {
public:
    static constexpr uint64_t kKept = 1024;

    void went(uint32_t id) {
        std::lock_guard<std::mutex> lk(mu_);
        ids_[n_ % kKept] = id;
        n_++;
    }

    uint64_t count() const {
        std::lock_guard<std::mutex> lk(mu_);
        return n_;
    }

    bool gone_since(uint32_t id, uint64_t since) const {
        std::lock_guard<std::mutex> lk(mu_);
        if (!id || since > n_ || n_ - since > kKept) return true;
        for (uint64_t i = since; i < n_; i++)
            if (ids_[i % kKept] == id) return true;
        return false;
    }

private:
    mutable std::mutex mu_;
    uint32_t ids_[kKept] = {};
    uint64_t n_ = 0;
};

}  // namespace texture_gone
