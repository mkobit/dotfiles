// snipctl — add/remove macOS Text Replacements through keyboardservicesd's own
// XPC service (_KSTextReplacementClientStore in the private KeyboardServices
// framework). This is the same path System Settings uses.
//
// The daemon accepts these calls from a normal (ad-hoc-signed) binary. Do NOT
// codesign this with the com.apple.keyboardservices.textreplacement.allow
// entitlement — falsely claiming that restricted entitlement makes the daemon
// reject the connection.
//
//   snipctl add    <shortcut> <phrase>
//   snipctl remove <shortcut> <phrase>
//
// The completion handler may report "KSTextReplacementErrorDomain Code=0"; that
// is benign — the operation can still succeed. We treat code 0 as OK.
//
// Build:  clang -fobjc-arc -framework Foundation snipctl.m -o snipctl

#import <Foundation/Foundation.h>
#import <dlfcn.h>

@protocol KSEntry <NSObject>
- (void)setShortcut:(NSString *)s;
- (void)setPhrase:(NSString *)p;
- (void)setTimestamp:(NSDate *)d;
@end

@protocol KSClientStore <NSObject>
- (void)addEntries:(NSArray *)add
      removeEntries:(NSArray *)remove
withCompletionHandler:(void (^)(NSError *err))done;
@end

static NSError *await(void (^op)(void (^done)(NSError *))) {
    __block NSError *err = nil;
    dispatch_semaphore_t sem = dispatch_semaphore_create(0);
    op(^(NSError *e) { err = e; dispatch_semaphore_signal(sem); });
    if (dispatch_semaphore_wait(sem, dispatch_time(DISPATCH_TIME_NOW, 20 * NSEC_PER_SEC))) {
        fprintf(stderr, "error: timed out talking to keyboardservicesd\n");
        exit(1);
    }
    return err;
}

int main(int argc, const char *argv[]) {
    @autoreleasepool {
        if (!dlopen("/System/Library/PrivateFrameworks/KeyboardServices.framework/KeyboardServices", RTLD_NOW)) {
            fprintf(stderr, "error: cannot load KeyboardServices.framework\n");
            return 1;
        }
        Class EntryClass = NSClassFromString(@"_KSTextReplacementEntry");
        Class StoreClass = NSClassFromString(@"_KSTextReplacementClientStore");
        if (!EntryClass || !StoreClass) {
            fprintf(stderr, "error: KeyboardServices private classes not found "
                            "(macOS changed?)\n");
            return 1;
        }
        id<KSClientStore> store = [[StoreClass alloc] init];

        NSString *cmd = argc >= 2 ? @(argv[1]) : @"";
        BOOL isAdd = [cmd isEqualToString:@"add"];
        BOOL isRemove = [cmd isEqualToString:@"remove"];
        if ((!isAdd && !isRemove) || argc != 4) {
            fprintf(stderr, "usage: snipctl add|remove <shortcut> <phrase>\n");
            return 2;
        }

        id<KSEntry> entry = [[EntryClass alloc] init];
        [entry setShortcut:@(argv[2])];
        [entry setPhrase:@(argv[3])];
        [entry setTimestamp:[NSDate date]];

        NSArray *add = isAdd ? @[ entry ] : @[];
        NSArray *remove = isRemove ? @[ entry ] : @[];
        NSError *err = await(^(void (^done)(NSError *)) {
            [store addEntries:add removeEntries:remove withCompletionHandler:done];
        });
        if (err && err.code != 0) {
            fprintf(stderr, "%s error: %s\n", argv[1], err.description.UTF8String);
            return 1;
        }
        printf("%s %s\n", isAdd ? "added" : "removed", argv[2]);
        return 0;
    }
}
