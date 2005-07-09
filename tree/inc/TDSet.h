// @(#)root/tree:$Name:  $:$Id: TDSet.h,v 1.12 2005/05/12 12:15:24 rdm Exp $
// Author: Fons Rademakers   11/01/02

/*************************************************************************
 * Copyright (C) 1995-2001, Rene Brun and Fons Rademakers.               *
 * All rights reserved.                                                  *
 *                                                                       *
 * For the licensing terms see $ROOTSYS/LICENSE.                         *
 * For the list of contributors see $ROOTSYS/README/CREDITS.             *
 *************************************************************************/

#ifndef ROOT_TDSet
#define ROOT_TDSet


//////////////////////////////////////////////////////////////////////////
//                                                                      //
// TDSet                                                                //
//                                                                      //
// This class implements a data set to be used for PROOF processing.    //
// The TDSet defines the class of which objects will be processed,      //
// the directory in the file where the objects of that type can be      //
// found and the list of files to be processed. The files can be        //
// specified as logical file names (LFN's) or as physical file names    //
// (PFN's). In case of LFN's the resolution to PFN's will be done       //
// according to the currently active GRID interface.                    //
// Examples:                                                            //
//   TDSet treeset("TTree", "AOD");                                     //
//   treeset.Add("lfn:/alien.cern.ch/alice/prod2002/file1");            //
//   ...                                                                //
//   treeset.AddFriend(friendset);                                      //
//                                                                      //
// or                                                                   //
//                                                                      //
//   TDSet objset("MyEvent", "*", "/events");                           //
//   objset.Add("root://cms.cern.ch/user/prod2002/hprod_1.root");       //
//   ...                                                                //
//   objset.Add(set2003);                                               //
//                                                                      //
// Validity of file names will only be checked at processing time       //
// (typically on the PROOF master server), not at creation time.        //
//                                                                      //
//////////////////////////////////////////////////////////////////////////

#ifndef ROOT_TNamed
#include "TNamed.h"
#endif

#ifndef ROOT_TEventList
#include "TEventList.h"
#endif

#include <set>
#include <list>

class TList;
class TDSet;
class TEventList;
class TCut;
class TTree;
class TChain;
class TVirtualProof;
class TEventList;


class TDSetElement : public TObject {
public:
   typedef  std::list<std::pair<TDSetElement*, TString> > FriendsList_t;
private:
   TString          fFileName;   // physical or logical file name
   TString          fObjName;    // name of objects to be analyzed in this file
   TString          fDirectory;  // directory in file where to look for objects
   Long64_t         fFirst;      // first entry to process
   Long64_t         fNum;        // number of entries to process
   const TDSet     *fSet;        //! set to which element belongs
   TString          fMsd;        // mass storage domain name
   Long64_t         fTDSetOffset;// the global offset in the TDSet of the first
                                 // entry in this element
   TEventList      *fEventList;  // event list to be used in processing
   Bool_t           fValid;      // whether or not the input values are valid
   Long64_t         fEntries;    // total number of possible entries in file
   FriendsList_t    *fFriends;    // friend elements
   Bool_t           fOwnerOfFriends;      // if true then all the TDSets in the friendship
                                          // graph will be deleted in the destructor

public:
   TDSetElement() { fSet = 0;  fValid = kFALSE; fEventList = 0; fFriends = 0; fOwnerOfFriends = kFALSE; }
   TDSetElement(const TDSet *set, const char *file, const char *objname = 0,
                const char *dir = 0, Long64_t first = 0, Long64_t num = -1,
                const char *msd = 0);
   virtual ~TDSetElement();

   virtual FriendsList_t *GetListOfFriends() const { return fFriends; }
   virtual void     AddFriend(TDSetElement *friendElement, const char* alias);
   virtual void     DeleteFriends();
   const char      *GetFileName() const { return fFileName; }
   Long64_t         GetFirst() const { return fFirst; }
   void             SetFirst(Long64_t first) { fFirst = first; }
   Long64_t         GetNum() const { return fNum; }
   const char      *GetMsd() const { return fMsd; }
   void             SetNum(Long64_t num) { fNum = num; }
   Bool_t           GetValid() const { return fValid; }
   const char      *GetObjName() const;
   const char      *GetDirectory() const;
   void             Print(Option_t *options="") const;
   Long64_t         GetTDSetOffset() const { return fTDSetOffset; }
   void             SetTDSetOffset(Long64_t offset) { fTDSetOffset = offset; }
   TEventList      *GetEventList() const { return fEventList; }
   void             SetEventList(TEventList *aList) { fEventList = aList; }
   void             Validate();
   void             Validate(TDSetElement *elem);
   Int_t            Compare(const TObject *obj) const;
   Bool_t           IsSortable() const { return kTRUE; }
   void             SetSet(TDSet* set) { fSet = set; }
   const TDSet     *GetSet() const { return fSet; }

   ClassDef(TDSetElement,3)  // A TDSet element
};


class TDSet : public TNamed {
public:
   typedef  std::list<std::pair<TDSet*, TString> > FriendsList_t;

private:
   TString        fObjName;     // name of objects to be analyzed (e.g. TTree name)
   TList         *fElements;    //-> list of TDSetElements
   Bool_t         fIsTree;      // true if type is a TTree (or TTree derived)
   TIter         *fIterator;    //! iterator on fElements
   TEventList    *fEventList; //! event list for processing
   FriendsList_t *fFriends;   // friend elements
   TDSet(const TDSet &);           // not implemented
   void operator=(const TDSet &);  // not implemented

protected:
   TDSetElement  *fCurrent;  //! current element

public:
   TDSet();
   TDSet(const char *type, const char *objname = "*", const char *dir = "/");
   virtual ~TDSet();

   virtual Bool_t        Add(const char *file, const char *objname = 0,
                             const char *dir = 0, Long64_t first = 0,
                             Long64_t num = -1, const char *msd = 0);
   virtual Bool_t        Add(TDSet *set);
   virtual void          AddFriend(TDSet *friendset, const char* alias);
   virtual void          DeleteFriends();
   virtual FriendsList_t *GetListOfFriends() const { return fFriends; } // may be null !

   virtual Int_t         Process(const char *selector, Option_t *option = "",
                                 Long64_t nentries = -1,
                                 Long64_t firstentry = 0,
                                 TEventList *evl = 0); // *MENU*
   virtual Int_t         Draw(const char *varexp, const char *selection,
                              Option_t *option = "", Long64_t nentries = -1,
                              Long64_t firstentry = 0); // *MENU*
   virtual Int_t         Draw(const char *varexp, const TCut &selection,
                              Option_t *option = "", Long64_t nentries = -1,
                              Long64_t firstentry = 0); // *MENU*
   virtual void          Draw(Option_t *opt) { Draw(opt, "", "", 1000000000, 0); }

   void                  Print(Option_t *option="") const;

   void                  SetObjName(const char *objname);
   void                  SetDirectory(const char *dir);

   Bool_t                IsTree() const { return fIsTree; }
   Bool_t                IsValid() const { return !fName.IsNull(); }
   Bool_t                ElementsValid() const;
   const char           *GetType() const { return fName; }
   const char           *GetObjName() const { return fObjName; }
   const char           *GetDirectory() const { return fTitle; }
   TList                *GetListOfElements() const { return fElements; }

   virtual void          Reset();
   virtual TDSetElement *Next();
   TDSetElement         *Current() const { return fCurrent; };

   static Long64_t       GetEntries(Bool_t isTree, const char *filename,
                                    const char *path, const char *objname);

   void                  AddInput(TObject *obj);
   void                  ClearInput();
   TObject              *GetOutput(const char *name);
   TList                *GetOutputList();
   virtual void          StartViewer(); // *MENU*

   virtual TTree        *GetTreeHeader(TVirtualProof *proof);
   virtual void          SetEventList(TEventList* evl) { fEventList = evl;}
   TEventList           *GetEventList() const {return fEventList; }
   void                  Validate();
   void                  Validate(TDSet *dset);

   ClassDef(TDSet,2)  // Data set for remote processing (PROOF)
};

#endif
